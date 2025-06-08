-- Fix Voting System Database Tables
-- Run this script to update your existing database to support the voting system
-- This script is safe to run multiple times

-- 1. Create Message_v2 table if it doesn't exist
CREATE TABLE IF NOT EXISTS "Message_v2" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "chatId" UUID NOT NULL REFERENCES "Chat"(id) ON DELETE CASCADE,
  role VARCHAR NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  parts JSON NOT NULL,
  attachments JSON NOT NULL,
  "createdAt" TIMESTAMP DEFAULT NOW()
);

-- 2. Create Vote_v2 table if it doesn't exist
CREATE TABLE IF NOT EXISTS "Vote_v2" (
  "chatId" UUID NOT NULL REFERENCES "Chat"(id) ON DELETE CASCADE,
  "messageId" UUID NOT NULL REFERENCES "Message_v2"(id) ON DELETE CASCADE,
  "isUpvoted" BOOLEAN NOT NULL,
  PRIMARY KEY ("chatId", "messageId")
);

-- 3. Add foreign key constraint to legacy Vote table if it exists
DO $$ BEGIN
 IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Vote' AND table_schema = 'public') THEN
   BEGIN
     ALTER TABLE "Vote" ADD CONSTRAINT "Vote_messageId_Message_id_fk" 
     FOREIGN KEY ("messageId") REFERENCES "Message"(id) ON DELETE CASCADE;
   EXCEPTION
     WHEN duplicate_object THEN null;
   END;
 END IF;
END $$;

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_message_v2_chat_id ON "Message_v2"("chatId");
CREATE INDEX IF NOT EXISTS idx_message_v2_created_at ON "Message_v2"("createdAt");
CREATE INDEX IF NOT EXISTS idx_message_v2_role ON "Message_v2"(role);

CREATE INDEX IF NOT EXISTS idx_vote_v2_chat_id ON "Vote_v2"("chatId");
CREATE INDEX IF NOT EXISTS idx_vote_v2_message_id ON "Vote_v2"("messageId");

-- 5. Migrate existing messages from Message to Message_v2 (if any exist)
-- This converts content field to parts JSON format
DO $$ BEGIN
 IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Message' AND table_schema = 'public') THEN
   INSERT INTO "Message_v2" (id, "chatId", role, parts, attachments, "createdAt")
   SELECT 
     id,
     "chatId",
     role,
     CASE 
       WHEN content IS NOT NULL THEN 
         ('[{"type": "text", "text": "' || REPLACE(REPLACE(content, '"', '\"'), E'\n', '\\n') || '"}]')::json
       ELSE 
         '[]'::json
     END as parts,
     '[]'::json as attachments,
     "createdAt"
   FROM "Message"
   WHERE NOT EXISTS (
     SELECT 1 FROM "Message_v2" WHERE "Message_v2".id = "Message".id
   );
 END IF;
END $$;

-- 6. Display results
SELECT 'Database tables updated successfully!' as status;

-- Show table counts (only for tables that exist)
WITH table_counts AS (
  SELECT 'Message_v2' as table_name, COUNT(*) as record_count FROM "Message_v2"
  UNION ALL
  SELECT 'Vote_v2' as table_name, COUNT(*) as record_count FROM "Vote_v2"
)
SELECT * FROM table_counts
UNION ALL
SELECT 'Message (legacy)' as table_name, 0 as record_count WHERE NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Message' AND table_schema = 'public')
UNION ALL  
SELECT 'Vote (legacy)' as table_name, 0 as record_count WHERE NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Vote' AND table_schema = 'public');