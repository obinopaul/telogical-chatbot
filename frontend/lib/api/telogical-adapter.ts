/**
 * Telogical API Adapter
 * 
 * This adapter connects the frontend to the Telogical backend API.
 * It translates between the frontend's AI SDK expectations and the backend's API format.
 */

import { type Message } from 'ai';
import { env } from 'process';

// Backend API endpoint - can be configured in .env
const API_BASE_URL = process.env.TELOGICAL_API_URL || 'http://localhost:8081';
const DEFAULT_AGENT = 'telogical-assistant';

/**
 * Converts frontend Message format to Telogical backend ChatMessage format
 */
export function convertToTelogicalFormat(messages: Message[]) {
  return messages.map(msg => ({
    type: msg.role === 'user' ? 'human' : 'ai',
    content: msg.content,
    id: msg.id,
    // Include attachments if available
    ...(msg.attachments ? { attachments: msg.attachments } : {})
  }));
}

/**
 * Makes a request to the Telogical backend API
 */
export async function callTelogicalAPI(
  messages: Message[],
  options: {
    stream?: boolean;
    agent?: string;
    model?: string;
    threadId?: string;
    userId?: string;
  } = {}
) {
  const {
    stream = false,
    agent = DEFAULT_AGENT,
    model = undefined,
    threadId = undefined,
    userId = undefined
  } = options;

  // Convert messages to Telogical format
  const telogicalMessages = convertToTelogicalFormat(messages);
  
  // Extract the last user message
  const lastUserMessage = messages.findLast(msg => msg.role === 'user');
  
  if (!lastUserMessage) {
    throw new Error('No user message found');
  }

  // Create the request body
  const requestBody = {
    message: lastUserMessage.content,
    model,
    thread_id: threadId,
    user_id: userId,
    agent_config: {
      message_history: telogicalMessages.slice(0, -1),
      show_reasoning: true
    }
  };

  // Determine the endpoint based on streaming preference
  const endpoint = stream ? `${API_BASE_URL}/${agent}/stream` : `${API_BASE_URL}/${agent}/invoke`;

  // Make the request
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    throw new Error(`Telogical API request failed: ${response.statusText}`);
  }

  return response;
}

/**
 * Process a streaming response from the Telogical backend
 */
export async function* processTelogicalStream(response: Response) {
  if (!response.body) {
    throw new Error('Response body is null');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      
      // Process SSE format: each event starts with 'data: ' and ends with '\n\n'
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') continue;
          
          try {
            const parsed = JSON.parse(data);
            
            // Yield tokens for the UI to display
            if (typeof parsed === 'string') {
              yield { type: 'token', token: parsed };
            } 
            // Yield reasoning data
            else if (parsed.type === 'reasoning') {
              yield { 
                type: 'reasoning', 
                content: parsed.content 
              };
            } 
            // Yield tool call data
            else if (parsed.type === 'tool') {
              yield { 
                type: 'tool', 
                name: parsed.name,
                input: parsed.input,
                output: parsed.output 
              };
            } 
            // Yield complete message
            else if (parsed.content !== undefined) {
              yield { 
                type: 'message',
                message: {
                  id: parsed.id || Date.now().toString(),
                  role: 'assistant',
                  content: parsed.content,
                  createdAt: new Date()
                }
              };
            }
          } catch (e) {
            console.error('Error parsing SSE data', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error reading stream', error);
    throw error;
  } finally {
    reader.releaseLock();
  }
}