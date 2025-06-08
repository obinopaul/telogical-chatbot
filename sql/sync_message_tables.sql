-- REAL-TIME SYNC SOLUTION
-- This ensures both Message and Message_v2 tables stay synchronized
-- Run this to fix the current issue and prevent future mismatches

-- Step 1: Copy any new messages from Message_v2 to Message
INSERT INTO "Message" (id, "chatId", role, parts, attachments, "createdAt")
SELECT id, "chatId", role, parts, attachments, "createdAt"
FROM "Message_v2" 
WHERE NOT EXISTS (
    SELECT 1 FROM "Message" WHERE "Message".id = "Message_v2".id
);

-- Step 2: Copy any new messages from Message to Message_v2 (bidirectional sync)
INSERT INTO "Message_v2" (id, "chatId", role, parts, attachments, "createdAt")
SELECT id, "chatId", role, parts, attachments, "createdAt"
FROM "Message" 
WHERE NOT EXISTS (
    SELECT 1 FROM "Message_v2" WHERE "Message_v2".id = "Message".id
);

-- Step 3: Create triggers for automatic bidirectional sync (optional)
-- This ensures any new message in either table automatically appears in both

-- Trigger function to sync from Message to Message_v2
CREATE OR REPLACE FUNCTION sync_message_to_v2() 
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO "Message_v2" (id, "chatId", role, parts, attachments, "createdAt")
    VALUES (NEW.id, NEW."chatId", NEW.role, NEW.parts, NEW.attachments, NEW."createdAt")
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger function to sync from Message_v2 to Message
CREATE OR REPLACE FUNCTION sync_message_from_v2() 
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO "Message" (id, "chatId", role, parts, attachments, "createdAt")
    VALUES (NEW.id, NEW."chatId", NEW.role, NEW.parts, NEW.attachments, NEW."createdAt")
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the triggers
DROP TRIGGER IF EXISTS trigger_sync_message_to_v2 ON "Message";
CREATE TRIGGER trigger_sync_message_to_v2
    AFTER INSERT ON "Message"
    FOR EACH ROW EXECUTE FUNCTION sync_message_to_v2();

DROP TRIGGER IF EXISTS trigger_sync_message_from_v2 ON "Message_v2";
CREATE TRIGGER trigger_sync_message_from_v2
    AFTER INSERT ON "Message_v2"
    FOR EACH ROW EXECUTE FUNCTION sync_message_from_v2();

-- Step 4: Verify sync worked
SELECT 'Sync completed! Table status:' as result;
SELECT 'Message table' as table_name, COUNT(*) as record_count FROM "Message"
UNION ALL
SELECT 'Message_v2 table' as table_name, COUNT(*) as record_count FROM "Message_v2"
UNION ALL
SELECT 'Vote table' as table_name, COUNT(*) as record_count FROM "Vote";

-- Step 5: Check if the missing message is now available
SELECT 'Missing message check:' as info;
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM "Message" WHERE id = '0adbfc84-80f4-4d22-a543-81933c0ed8b5') 
        THEN 'Found in Message table ✅'
        ELSE 'Still missing from Message table ❌'
    END as message_status;