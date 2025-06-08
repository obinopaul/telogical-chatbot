-- Final consolidation: Ensure only Message table exists and is used
-- This prevents any confusion between Message and Message_v2

-- First ensure all data is in the Message table
INSERT INTO "Message" (id, "chatId", role, parts, attachments, "createdAt")
SELECT id, "chatId", role, parts, attachments, "createdAt"
FROM "Message_v2" 
WHERE NOT EXISTS (
    SELECT 1 FROM "Message" WHERE "Message".id = "Message_v2".id
) ON CONFLICT (id) DO NOTHING;

-- Drop the old tables to prevent confusion
DROP TABLE IF EXISTS "Vote_v2" CASCADE;
DROP TABLE IF EXISTS "Message_v2" CASCADE;

-- Ensure Vote table exists and references Message table
CREATE TABLE IF NOT EXISTS "Vote" (
    "chatId" UUID NOT NULL REFERENCES "Chat"(id) ON DELETE CASCADE,
    "messageId" UUID NOT NULL REFERENCES "Message"(id) ON DELETE CASCADE,
    "isUpvoted" BOOLEAN NOT NULL,
    PRIMARY KEY ("chatId", "messageId")
);

-- Remove any existing sync triggers that might be confusing the system
DROP TRIGGER IF EXISTS trigger_sync_message_to_v2 ON "Message";
DROP TRIGGER IF EXISTS trigger_sync_message_from_v2 ON "Message_v2";
DROP FUNCTION IF EXISTS sync_message_to_v2();
DROP FUNCTION IF EXISTS sync_message_from_v2();

-- Final verification
SELECT 'Consolidation complete - only Message table remains!' as status;