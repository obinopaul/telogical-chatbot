-- Telogical Chatbot Database Initialization
-- This script creates all required tables and indexes for production deployment
-- Run this script on your PostgreSQL database before deploying

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create User table for authentication
CREATE TABLE IF NOT EXISTS "User" (
  id VARCHAR PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255),
  name VARCHAR(255),
  image TEXT,
  "createdAt" TIMESTAMP DEFAULT NOW()
);

-- Create Chat table for conversation history
CREATE TABLE IF NOT EXISTS "Chat" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "createdAt" TIMESTAMP NOT NULL DEFAULT NOW(),
  title TEXT NOT NULL,
  "userId" VARCHAR NOT NULL REFERENCES "User"(id) ON DELETE CASCADE,
  visibility VARCHAR DEFAULT 'private' CHECK (visibility IN ('private', 'public'))
);

-- Create Message table for chat messages
CREATE TABLE IF NOT EXISTS "Message" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "chatId" UUID NOT NULL REFERENCES "Chat"(id) ON DELETE CASCADE,
  role VARCHAR NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  "createdAt" TIMESTAMP DEFAULT NOW()
);

-- Create Document table for RAG/file uploads (optional)
CREATE TABLE IF NOT EXISTS "Document" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "userId" VARCHAR NOT NULL REFERENCES "User"(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  content TEXT,
  "mimeType" VARCHAR(100),
  size INTEGER,
  "createdAt" TIMESTAMP DEFAULT NOW()
);

-- Create Vote table for message feedback (optional)
CREATE TABLE IF NOT EXISTS "Vote" (
  "chatId" UUID NOT NULL REFERENCES "Chat"(id) ON DELETE CASCADE,
  "messageId" UUID NOT NULL,
  "isUpvoted" BOOLEAN NOT NULL,
  PRIMARY KEY ("chatId", "messageId")
);

-- Create Suggestion table for suggested actions (optional)
CREATE TABLE IF NOT EXISTS "Suggestion" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "documentId" UUID REFERENCES "Document"(id) ON DELETE CASCADE,
  "userId" VARCHAR NOT NULL REFERENCES "User"(id) ON DELETE CASCADE,
  "originalText" TEXT NOT NULL,
  "suggestedText" TEXT NOT NULL,
  description TEXT,
  "isResolved" BOOLEAN DEFAULT FALSE,
  "createdAt" TIMESTAMP DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_email ON "User"(email);
CREATE INDEX IF NOT EXISTS idx_user_created_at ON "User"("createdAt");

CREATE INDEX IF NOT EXISTS idx_chat_user_id ON "Chat"("userId");
CREATE INDEX IF NOT EXISTS idx_chat_created_at ON "Chat"("createdAt");
CREATE INDEX IF NOT EXISTS idx_chat_visibility ON "Chat"(visibility);

CREATE INDEX IF NOT EXISTS idx_message_chat_id ON "Message"("chatId");
CREATE INDEX IF NOT EXISTS idx_message_created_at ON "Message"("createdAt");
CREATE INDEX IF NOT EXISTS idx_message_role ON "Message"(role);

CREATE INDEX IF NOT EXISTS idx_document_user_id ON "Document"("userId");
CREATE INDEX IF NOT EXISTS idx_document_created_at ON "Document"("createdAt");
CREATE INDEX IF NOT EXISTS idx_document_mime_type ON "Document"("mimeType");

CREATE INDEX IF NOT EXISTS idx_vote_chat_id ON "Vote"("chatId");
CREATE INDEX IF NOT EXISTS idx_vote_message_id ON "Vote"("messageId");

CREATE INDEX IF NOT EXISTS idx_suggestion_document_id ON "Suggestion"("documentId");
CREATE INDEX IF NOT EXISTS idx_suggestion_user_id ON "Suggestion"("userId");
CREATE INDEX IF NOT EXISTS idx_suggestion_resolved ON "Suggestion"("isResolved");

-- Insert default/test users (optional - remove in production)
INSERT INTO "User" (id, email, name, "createdAt")
VALUES 
  ('default-user-001', 'admin@telogical.com', 'System Administrator', NOW()),
  ('test-user-001', 'test@telogical.com', 'Test User', NOW())
ON CONFLICT (email) DO NOTHING;

-- Create a sample chat for testing (optional - remove in production)
INSERT INTO "Chat" (id, title, "userId", "createdAt")
VALUES 
  ('550e8400-e29b-41d4-a716-446655440000', 'Welcome Chat', 'default-user-001', NOW())
ON CONFLICT (id) DO NOTHING;

-- Insert welcome message (optional - remove in production)
INSERT INTO "Message" ("chatId", role, content, "createdAt")
VALUES 
  ('550e8400-e29b-41d4-a716-446655440000', 'assistant', 'Welcome to Telogical AI Assistant! I''m here to help you with telecom market intelligence questions. How can I assist you today?', NOW())
ON CONFLICT (id) DO NOTHING;

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Display table information
SELECT 
  table_name,
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name IN ('User', 'Chat', 'Message', 'Document', 'Vote', 'Suggestion')
ORDER BY table_name, ordinal_position;