/**
 * Telogical Custom Provider
 * 
 * This file defines a custom AI provider that connects to the Telogical backend.
 * It implements the necessary language model interfaces required by the AI SDK.
 */

import { customProvider } from 'ai';
import { callTelogicalAPI, processTelogicalStream } from '../api/telogical-adapter';
import { type Message } from 'ai';

interface TelogicalStreamResult {
  type: 'token' | 'reasoning' | 'tool' | 'message';
  token?: string;
  content?: string;
  name?: string;
  input?: string;
  output?: string;
  message?: Message;
}

/**
 * Creates a language model that interfaces with the Telogical backend
 */
function createTelogicalLanguageModel(agent: string = 'telogical-assistant') {
  return {
    // Required LanguageModelV1 properties
    specificationVersion: 'v1',
    provider: 'telogical',
    modelId: agent,
    defaultObjectGenerationMode: 'json' as const,
    supportsImageInput: false,
    supportsObjectGeneration: false,
    
    // Non-streaming call implementation
    async invoke({ messages }: { messages: Message[] }) {
      const response = await callTelogicalAPI(messages, { agent });
      const data = await response.json();
      
      return {
        messages: [
          ...messages,
          {
            id: data.id || Date.now().toString(),
            role: 'assistant',
            content: data.content
          }
        ],
        usage: data.usage || null,
        data: data.custom_data || {}
      };
    },
    
    // Streaming call implementation
    async *stream({ messages }: { messages: Message[] }) {
      let responseText = '';
      let reasoning = '';
      let toolCalls: any[] = [];
      
      const response = await callTelogicalAPI(messages, { 
        stream: true, 
        agent 
      });
      
      const streamGenerator = processTelogicalStream(response);
      
      for await (const item of streamGenerator) {
        const result = item as TelogicalStreamResult;
        
        // Process tokens (text content)
        if (result.type === 'token' && result.token) {
          responseText += result.token;
          yield {
            messages: [
              ...messages,
              {
                id: Date.now().toString(),
                role: 'assistant',
                content: responseText
              }
            ],
            usage: null,
            data: {
              reasoning,
              toolCalls
            }
          };
        } 
        // Process reasoning information
        else if (result.type === 'reasoning' && result.content) {
          reasoning = result.content;
          yield {
            messages: [
              ...messages,
              {
                id: Date.now().toString(),
                role: 'assistant',
                content: responseText
              }
            ],
            usage: null,
            data: {
              reasoning,
              toolCalls
            }
          };
        } 
        // Process tool call information
        else if (result.type === 'tool' && result.name) {
          toolCalls.push({
            name: result.name,
            input: result.input || '',
            output: result.output || ''
          });
          yield {
            messages: [
              ...messages,
              {
                id: Date.now().toString(),
                role: 'assistant',
                content: responseText
              }
            ],
            usage: null,
            data: {
              reasoning,
              toolCalls
            }
          };
        }
        // Process complete message (if any)
        else if (result.type === 'message' && result.message) {
          yield {
            messages: [
              ...messages,
              result.message
            ],
            usage: null,
            data: {
              reasoning,
              toolCalls
            }
          };
        }
      }
    }
  };
}

/**
 * Creates a telogical provider that can be used with the AI SDK
 */
export const telogicalProvider = customProvider({
  languageModels: {
    'chat-model': createTelogicalLanguageModel('telogical-assistant'),
    'chat-model-reasoning': createTelogicalLanguageModel('telogical-assistant'),
    'title-model': createTelogicalLanguageModel('telogical-assistant'),
    'artifact-model': createTelogicalLanguageModel('telogical-assistant'),
    'telogical-assistant': createTelogicalLanguageModel('telogical-assistant'),
    'research-assistant': createTelogicalLanguageModel('research-assistant'),
  }
});