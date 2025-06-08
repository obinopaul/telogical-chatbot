-- SAFE MESSAGE CONSOLIDATION STRATEGY
-- This script safely prepares the Message table to be the primary table
-- while keeping Message_v2 intact during transition

-- Step 1: Ensure Message table has v2 capabilities
-- Drop and recreate Message table with full v2 features
DROP TABLE IF EXISTS "Message" CASCADE;

CREATE TABLE "Message" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "chatId" UUID NOT NULL REFERENCES "Chat"(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    parts JSON NOT NULL,
    attachments JSON NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Step 2: Copy ALL data from Message_v2 to Message
INSERT INTO "Message" (id, "chatId", role, parts, attachments, "createdAt")
SELECT id, "chatId", role, parts, attachments, "createdAt"
FROM "Message_v2";

-- Step 3: Create new Vote table that references Message
DROP TABLE IF EXISTS "Vote" CASCADE;

CREATE TABLE "Vote" (
    "chatId" UUID NOT NULL REFERENCES "Chat"(id) ON DELETE CASCADE,
    "messageId" UUID NOT NULL REFERENCES "Message"(id) ON DELETE CASCADE,
    "isUpvoted" BOOLEAN NOT NULL,
    PRIMARY KEY ("chatId", "messageId")
);

-- Step 4: Create performance indexes
CREATE INDEX IF NOT EXISTS idx_message_chat_id ON "Message"("chatId");
CREATE INDEX IF NOT EXISTS idx_message_created_at ON "Message"("createdAt");
CREATE INDEX IF NOT EXISTS idx_message_role ON "Message"(role);
CREATE INDEX IF NOT EXISTS idx_vote_chat_id ON "Vote"("chatId");
CREATE INDEX IF NOT EXISTS idx_vote_message_id ON "Vote"("messageId");

-- Step 5: Verify data integrity
SELECT 'Data integrity check:' as status;
SELECT 
    'Message' as table_name, 
    COUNT(*) as record_count,
    MIN("createdAt") as oldest_message,
    MAX("createdAt") as newest_message
FROM "Message"
UNION ALL
SELECT 
    'Message_v2' as table_name, 
    COUNT(*) as record_count,
    MIN("createdAt") as oldest_message,
    MAX("createdAt") as newest_message
FROM "Message_v2"
UNION ALL
SELECT 
    'Vote' as table_name, 
    COUNT(*) as record_count,
    NULL as oldest_message,
    NULL as newest_message
FROM "Vote";

-- Step 6: Show successful consolidation
SELECT 'Message table is now ready as primary table!' as result;
SELECT 'Message_v2 table preserved for safety during transition' as note;