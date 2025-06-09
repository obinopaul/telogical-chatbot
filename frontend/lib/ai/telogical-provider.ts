/**
 * Telogical Custom Provider
 * 
 * This file defines a custom AI provider that connects to the Telogical backend.
 * It implements the necessary language model interfaces required by the AI SDK.
 */

import { customProvider } from 'ai';
import { callTelogicalAPI, processTelogicalStream } from '../api/telogical-adapter';
import { type Message } from 'ai';
import type { LanguageModelV1, LanguageModelV1FinishReason } from '@ai-sdk/provider';

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
function createTelogicalLanguageModel(agent: string = 'telogical-assistant'): LanguageModelV1 {
  return {
    // Required LanguageModelV1 metadata properties
    specificationVersion: 'v1',
    provider: 'telogical',
    modelId: agent,
    defaultObjectGenerationMode: 'json',
    supportsImageInput: false,
    
    // Required LanguageModelV1 core methods
    async doGenerate(options) {
      // Convert messages to prompt string for our API
      const prompt = Array.isArray(options.prompt) 
        ? options.prompt.map((msg: any) => `${msg.role}: ${msg.content}`).join('\n')
        : options.prompt;
      
      const requestPayload = [{ role: 'user', content: prompt }];
      const response = await callTelogicalAPI(requestPayload, { agent });
      const data = await response.json();
      
      return {
        text: data.content || '',
        toolCalls: [],
        toolResults: [],
        finishReason: 'stop' as LanguageModelV1FinishReason,
        usage: {
          promptTokens: Math.ceil(prompt.length / 4),
          completionTokens: Math.ceil((data.content || '').length / 4)
        },
        warnings: undefined,
        rawCall: {
          rawPrompt: prompt,
          rawSettings: { agent },
          requestBodyValues: requestPayload
        },
        logprobs: undefined,
        reasoning: undefined,
        request: {
          body: JSON.stringify(requestPayload)
        },
        response: {
          headers: response.headers ? Object.fromEntries(response.headers.entries()) : {},
          body: JSON.stringify(data)
        }
      };
    },
    
    async doStream(options) {
      // Convert messages to prompt string for our API
      const prompt = Array.isArray(options.prompt) 
        ? options.prompt.map((msg: any) => `${msg.role}: ${msg.content}`).join('\n')
        : options.prompt;
      
      const requestPayload = [{ role: 'user', content: prompt }];
      
      const streamGen = async function* () {
        let responseText = '';
        
        const response = await callTelogicalAPI(requestPayload, { 
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
              type: 'text-delta',
              textDelta: result.token
            };
          }
        }
        
        // Final completion
        yield {
          type: 'finish',
          finishReason: 'stop' as LanguageModelV1FinishReason,
          usage: { 
            promptTokens: Math.ceil(prompt.length / 4), 
            completionTokens: Math.ceil(responseText.length / 4)
          },
          logprobs: undefined,
          rawCall: {
            rawPrompt: prompt,
            rawSettings: { agent },
            requestBodyValues: requestPayload
          }
        };
      };
      
      return {
        stream: streamGen(),
        warnings: undefined,
        rawCall: {
          rawPrompt: prompt,
          rawSettings: { agent },
          requestBodyValues: requestPayload
        }
      };
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