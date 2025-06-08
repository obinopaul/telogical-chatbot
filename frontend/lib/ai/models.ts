export const DEFAULT_CHAT_MODEL: string = 'telogical-assistant';

export interface ChatModel {
  id: string;
  name: string;
  description: string;
}

export const chatModels: Array<ChatModel> = [
  {
    id: 'telogical-assistant',
    name: 'Telogical Assistant',
    description: 'AI assistant for telecom market intelligence',
  },
  {
    id: 'research-assistant',
    name: 'Research Assistant',
    description: 'General research assistant with search capabilities',
  },
  {
    id: 'chat-model',
    name: 'Chat model',
    description: 'Primary model for all-purpose chat',
  },
  {
    id: 'chat-model-reasoning',
    name: 'Reasoning model',
    description: 'Uses advanced reasoning',
  },
];
