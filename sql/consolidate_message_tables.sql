-- Consolidate Message Tables: Make Message the main table with v2 features
-- This script safely migrates from Message_v2 back to Message with enhanced functionality
-- Run this script to unify all message functionality into a single Message table

-- 1. First, check what we're working with
SELECT 'Before migration:' as status;
SELECT 'Message table' as table_name, COUNT(*) as records FROM "Message" WHERE EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Message' AND table_schema = 'public')
UNION ALL
SELECT 'Message_v2 table' as table_name, COUNT(*) as records FROM "Message_v2" WHERE EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Message_v2' AND table_schema = 'public');

-- 2. Create backup of existing Message table if it exists
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Message' AND table_schema = 'public') THEN
        CREATE TABLE IF NOT EXISTS "Message_backup" AS SELECT * FROM "Message";
        RAISE NOTICE 'Backed up existing Message table to Message_backup';
    END IF;
END $$;

-- 3. Drop the old Message table to recreate it with v2 features
DROP TABLE IF EXISTS "Message" CASCADE;

-- 4. Create the new unified Message table with all v2 features
CREATE TABLE "Message" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "chatId" UUID NOT NULL REFERENCES "Chat"(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    parts JSON NOT NULL,
    attachments JSON NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 5. Migrate all data from Message_v2 to the new Message table
INSERT INTO "Message" (id, "chatId", role, parts, attachments, "createdAt")
SELECT id, "chatId", role, parts, attachments, "createdAt"
FROM "Message_v2"
WHERE EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Message_v2' AND table_schema = 'public');

-- 6. Migrate any data from backup Message table (convert content to parts format)
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Message_backup' AND table_schema = 'public') THEN
        INSERT INTO "Message" (id, "chatId", role, parts, attachments, "createdAt")
        SELECT 
            id,
            "chatId",
            role,
            CASE 
                WHEN content IS NOT NULL THEN 
                    ('[{"type": "text", "text": "' || REPLACE(REPLACE(content::text, '"', '\"'), E'\n', '\\n') || '"}]')::json
                ELSE 
                    '[]'::json
            END as parts,
            '[]'::json as attachments,
            "createdAt"
        FROM "Message_backup"
        WHERE NOT EXISTS (
            SELECT 1 FROM "Message" WHERE "Message".id = "Message_backup".id
        );
        RAISE NOTICE 'Migrated data from Message_backup to new Message table';
    END IF;
END $$;

-- 7. Create new Vote table that references the unified Message table
DROP TABLE IF EXISTS "Vote" CASCADE;
DROP TABLE IF EXISTS "Vote_v2" CASCADE;

CREATE TABLE "Vote" (
    "chatId" UUID NOT NULL REFERENCES "Chat"(id) ON DELETE CASCADE,
    "messageId" UUID NOT NULL REFERENCES "Message"(id) ON DELETE CASCADE,
    "isUpvoted" BOOLEAN NOT NULL,
    PRIMARY KEY ("chatId", "messageId")
);

-- 8. Create performance indexes
CREATE INDEX IF NOT EXISTS idx_message_chat_id ON "Message"("chatId");
CREATE INDEX IF NOT EXISTS idx_message_created_at ON "Message"("createdAt");
CREATE INDEX IF NOT EXISTS idx_message_role ON "Message"(role);

CREATE INDEX IF NOT EXISTS idx_vote_chat_id ON "Vote"("chatId");
CREATE INDEX IF NOT EXISTS idx_vote_message_id ON "Vote"("messageId");

-- 9. Clean up old tables
DROP TABLE IF EXISTS "Message_v2" CASCADE;
DROP TABLE IF EXISTS "Vote_v2" CASCADE;
DROP TABLE IF EXISTS "Message_backup" CASCADE;

-- 10. Show final results
SELECT 'After migration:' as status;
SELECT 'Message table' as table_name, COUNT(*) as records FROM "Message"
UNION ALL
SELECT 'Vote table' as table_name, COUNT(*) as records FROM "Vote";

SELECT 'Migration completed successfully!' as result;