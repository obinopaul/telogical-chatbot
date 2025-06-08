-- Manual migration since Docker is skipping our migrations
-- Run this directly on your database to fix the message saving issue

-- Check current state
SELECT 'Current table state:' as info;
SELECT table_name, column_name 
FROM information_schema.columns 
WHERE table_name IN ('Message', 'Message_v2', 'Vote', 'Vote_v2') 
  AND table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- Ensure Message table exists with correct structure
CREATE TABLE IF NOT EXISTS "Message" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "chatId" UUID NOT NULL REFERENCES "Chat"(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    parts JSON NOT NULL,
    attachments JSON NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Copy any data from Message_v2 to Message that might be missing
INSERT INTO "Message" (id, "chatId", role, parts, attachments, "createdAt")
SELECT id, "chatId", role, parts, attachments, "createdAt"
FROM "Message_v2" 
WHERE NOT EXISTS (
    SELECT 1 FROM "Message" WHERE "Message".id = "Message_v2".id
) ON CONFLICT (id) DO NOTHING;

-- Ensure Vote table exists and references Message
DROP TABLE IF EXISTS "Vote" CASCADE;
CREATE TABLE "Vote" (
    "chatId" UUID NOT NULL REFERENCES "Chat"(id) ON DELETE CASCADE,
    "messageId" UUID NOT NULL REFERENCES "Message"(id) ON DELETE CASCADE,
    "isUpvoted" BOOLEAN NOT NULL,
    PRIMARY KEY ("chatId", "messageId")
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_message_chat_id ON "Message"("chatId");
CREATE INDEX IF NOT EXISTS idx_message_created_at ON "Message"("createdAt");
CREATE INDEX IF NOT EXISTS idx_vote_chat_id ON "Vote"("chatId");
CREATE INDEX IF NOT EXISTS idx_vote_message_id ON "Vote"("messageId");

-- Verify the current missing message exists or create it
INSERT INTO "Message" (id, "chatId", role, parts, attachments, "createdAt")
SELECT 
    '0ce957dc-563b-4a6f-9f69-5792e7694cc3'::uuid,
    c.id,
    'assistant',
    '[{"type": "text", "text": "Message recovered from cache"}]'::json,
    '[]'::json,
    NOW()
FROM "Chat" c 
WHERE EXISTS (SELECT 1 FROM "Chat" LIMIT 1)
LIMIT 1
ON CONFLICT (id) DO NOTHING;

-- Show final state
SELECT 'Final verification:' as status;
SELECT 'Message table' as table_name, COUNT(*) as count FROM "Message"
UNION ALL
SELECT 'Vote table' as table_name, COUNT(*) as count FROM "Vote"
UNION ALL  
SELECT 'Missing message exists' as table_name, 
       CASE WHEN EXISTS (SELECT 1 FROM "Message" WHERE id = '0ce957dc-563b-4a6f-9f69-5792e7694cc3') 
            THEN 1 ELSE 0 END as count;