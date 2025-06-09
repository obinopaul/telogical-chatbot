/**
 * SIMPLE DIRECT BACKEND CONNECTION
 * No AI SDK complexity - just direct HTTP calls to your Telogical backend
 */

import { auth } from '@/app/(auth)/auth';
import { 
  getChatById, 
  saveChat, 
  saveMessages,
  getMessagesByChatId,
  createGuestUser,
  createQuestionHash,
  getCachedResponse,
  saveCachedResponse,
  incrementCacheHitCount
} from '@/lib/db/queries';
import { user, chat as chatTable } from '@/lib/db/schema';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { eq } from 'drizzle-orm';
import { ChatSDKError } from '@/lib/errors';
import { generateUUID } from '@/lib/utils';

export const maxDuration = 60;

export async function POST(request: Request) {
  try {
    const { id, message, selectedVisibilityType } = await request.json();
    
    const session = await auth();
    if (!session?.user) {
      return new ChatSDKError('unauthorized:chat').toResponse();
    }

    // User should already exist from Google OAuth sign-in
    // No need to create random users anymore

    // Create chat if it doesn't exist
    const chat = await getChatById({ id });
    if (!chat) {
      // Extract user question for title generation
      const userQuestion = Array.isArray(message.parts) ? 
        message.parts.map((p: any) => p.text || p).join('') : 
        message.content;
      
      // Generate title from first user message (max 50 characters)
      const chatTitle = userQuestion && userQuestion.length > 0
        ? (userQuestion.length > 50 
          ? userQuestion.substring(0, 47) + "..." 
          : userQuestion)
        : "New Chat";
      
      await saveChat({
        id,
        userId: session.user.id,
        title: chatTitle,
        visibility: selectedVisibilityType || 'private',
      });
    }

    // Save user message to database
    await saveMessages({
      messages: [{
        chatId: id,
        id: message.id,
        role: 'user',
        parts: message.parts,
        attachments: message.experimental_attachments ?? [],
        createdAt: new Date(),
      }],
    });

    // Extract user question for cache checking
    const userQuestion = Array.isArray(message.parts) ? 
      message.parts.map((p: any) => p.text || p).join('') : 
      message.content;

    // ======= CACHE CHECK =======
    const questionHash = createQuestionHash(userQuestion);
    const cachedResponse = await getCachedResponse({
      questionHash,
      userId: session.user.id,
      chatId: id,
    });

    if (cachedResponse) {
      console.log('💾 Cache HIT - returning cached response for chat:', id);
      
      // Increment cache hit counter
      await incrementCacheHitCount({
        questionHash,
        userId: session.user.id,
        chatId: id,
      });

      // Save assistant message from cache to current chat
      const assistantMessageId = generateUUID();
      await saveMessages({
        messages: [{
          chatId: id,
          id: assistantMessageId,
          role: 'assistant',
          parts: [{ type: 'text', text: cachedResponse.aiResponse }],
          attachments: [],
          createdAt: new Date(),
        }],
      });

      // Return cached response as stream
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          const streamData = `0:${JSON.stringify(cachedResponse.aiResponse)}\n`;
          controller.enqueue(encoder.encode(streamData));
          controller.close();
        }
      });

      return new Response(stream, {
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'x-vercel-ai-data-stream': 'v1',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive'
        }
      });
    }

    console.log('🔄 Cache MISS - calling backend');

    // Get all previous messages
    const previousMessages = await getMessagesByChatId({ id });
    
    // Convert to simple format for your backend, filtering ONLY user/assistant messages (exclude system, tool, etc.)
    const backendMessages = previousMessages
      .filter(msg => msg.role === 'user' || msg.role === 'assistant')
      .filter(msg => msg.role !== 'system') // Explicitly exclude system messages
      .map(msg => ({
        type: msg.role === 'user' ? 'human' : 'ai',
        content: Array.isArray(msg.parts) ? msg.parts.map(p => p.text || p).join('') : msg.parts,
      }));

    // Direct call to your backend with retry logic for rate limiting
    const makeBackendRequest = async (attempt = 1, maxRetries = 3): Promise<Response> => {
      try {
        const backendUrl = process.env.TELOGICAL_API_URL || 'http://backend:8081';
        const backendResponse = await fetch(`${backendUrl}/telogical-assistant/stream`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            // Add authorization header to authenticate with the backend
            'Authorization': `Bearer ${process.env.TELOGICAL_API_SECRET}`
          },
          body: JSON.stringify({
            message: Array.isArray(message.parts) ? message.parts.map((p: any) => p.text || p).join('') : message.content,
            agent_config: {
              message_history: backendMessages.slice(0, -1),
              show_reasoning: true
            }
          })
        });

        // If rate limited (429), retry with exponential backoff
        if (backendResponse.status === 429 && attempt < maxRetries) {
          const waitTime = Math.pow(2, attempt) * 1000; // 2s, 4s, 8s
          console.log(`🔄 Rate limited (429), retrying in ${waitTime}ms (attempt ${attempt}/${maxRetries})`);
          await new Promise(resolve => setTimeout(resolve, waitTime));
          return makeBackendRequest(attempt + 1, maxRetries);
        }

        return backendResponse;
      } catch (error) {
        if (attempt < maxRetries) {
          const waitTime = Math.pow(2, attempt) * 1000;
          console.log(`🔄 Request failed, retrying in ${waitTime}ms (attempt ${attempt}/${maxRetries})`);
          await new Promise(resolve => setTimeout(resolve, waitTime));
          return makeBackendRequest(attempt + 1, maxRetries);
        }
        throw error;
      }
    };

    const backendResponse = await makeBackendRequest();

    if (!backendResponse.ok) {
      throw new Error(`Backend error: ${backendResponse.statusText}`);
    }

    // Create AI SDK compatible streaming response
    let assistantMessageId = generateUUID(); // Use proper UUID format
    let fullResponse = '';
    let hasResponseBeenSent = false;
    
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        const reader = backendResponse.body?.getReader();
        const decoder = new TextDecoder();
        
        const pump = async () => {
          if (!reader) return;
          
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              
              const chunk = decoder.decode(value, { stream: true });
              const lines = chunk.split('\n');
              
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const data = line.slice(6);
                  if (data === '[DONE]') continue;
                  
                  try {
                    const parsed = JSON.parse(data);
                    
                    // Process final clean message from backend
                    if (parsed.type === 'message' && parsed.content && parsed.content.content) {
                      const messageContent = parsed.content.content;
                      // Relaxed filtering - only reject obvious non-content
                      if (!messageContent.includes('contextual_insights') && 
                          messageContent.trim().length > 10) {
                        fullResponse = messageContent;
                      }
                    } else if (parsed.type === 'error') {
                      console.error('Backend error:', parsed.content);
                      continue;
                    }
                  } catch (e) {
                    // Skip malformed JSON
                  }
                  
                  // Send response if we have content and haven't sent anything yet
                  if (fullResponse.trim() && !hasResponseBeenSent) {
                    const streamData = `0:${JSON.stringify(fullResponse)}\n`;
                    controller.enqueue(encoder.encode(streamData));
                    hasResponseBeenSent = true;
                  }
                }
              }
            }
            
            // Ensure we always send a response even if filtering missed it
            if (!hasResponseBeenSent && fullResponse.trim()) {
              const streamData = `0:${JSON.stringify(fullResponse)}\n`;
              controller.enqueue(encoder.encode(streamData));
              hasResponseBeenSent = true;
            }
            
            // Save assistant response to database (async, don't block stream)
            if (fullResponse.trim()) {
              saveMessages({
                messages: [{
                  chatId: id,
                  id: assistantMessageId,
                  role: 'assistant',
                  parts: [{ type: 'text', text: fullResponse }], // Match user message format
                  attachments: [],
                  createdAt: new Date(),
                }],
              }).catch(err => console.error('Failed to save assistant message:', err));

              // ======= SAVE TO CACHE =======
              console.log('💾 Saving response to cache');
              // Set cache expiration to 24 hours from now
              const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000);
              
              saveCachedResponse({
                questionHash,
                userQuestion,
                aiResponse: fullResponse,
                userId: session.user.id,
                chatId: id,
                expiresAt,
              }).catch(err => console.error('Failed to save to cache:', err));
            }
            
          } catch (error) {
            console.error('Stream error:', error);
          } finally {
            controller.close();
            reader.releaseLock();
          }
        };
        
        pump();
      }
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'x-vercel-ai-data-stream': 'v1',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      }
    });

  } catch (error) {
    console.error('Chat route error:', error);
    return new ChatSDKError('offline:api', 'Backend connection failed').toResponse();
  }
}

export async function GET(request: Request) {
  return new Response(null, { status: 204 });
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');

  if (!id) {
    return new ChatSDKError('bad_request:api').toResponse();
  }

  const session = await auth();
  if (!session?.user) {
    return new ChatSDKError('unauthorized:chat').toResponse();
  }

  // Simple delete implementation
  return Response.json({ success: true }, { status: 200 });
}