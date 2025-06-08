import {
  customProvider,
  extractReasoningMiddleware,
  wrapLanguageModel,
} from 'ai';
import { xai } from '@ai-sdk/xai';
import { isTestEnvironment } from '../constants';
import {
  artifactModel,
  chatModel,
  reasoningModel,
  titleModel,
} from './models.test';
import { telogicalProvider } from './telogical-provider';

// Determine if we should use the Telogical backend
const useTelogicalBackend = process.env.USE_TELOGICAL_BACKEND === 'true';

export const myProvider = isTestEnvironment
  ? customProvider({
      languageModels: {
        'chat-model': chatModel,
        'chat-model-reasoning': reasoningModel,
        'title-model': titleModel,
        'artifact-model': artifactModel,
      },
    })
  : useTelogicalBackend
    ? telogicalProvider
    : customProvider({
        languageModels: {
          'chat-model': xai('grok-2-vision-1212'),
          'chat-model-reasoning': wrapLanguageModel({
            model: xai('grok-3-mini-beta'),
            middleware: extractReasoningMiddleware({ tagName: 'think' }),
          }),
          'title-model': xai('grok-2-1212'),
          'artifact-model': xai('grok-2-1212'),
        },
        imageModels: {
          'small-model': xai.image('grok-2-image'),
        },
      });
