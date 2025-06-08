-- Debug script to find the missing message and understand the data structure

-- 1. Check if the specific message exists in any table
SELECT 'Searching for message: c0a66bcd-6692-4878-9112-a550c66d3fca' as info;

-- 2. Check in Message_v2 table
SELECT 'Message_v2 search:' as table_name, COUNT(*) as found
FROM "Message_v2" 
WHERE id = 'c0a66bcd-6692-4878-9112-a550c66d3fca';

-- 3. Check if legacy Message table exists and search there
DO $$ 
DECLARE
    message_count INTEGER := 0;
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Message' AND table_schema = 'public') THEN
        SELECT COUNT(*) INTO message_count FROM "Message" WHERE id = 'c0a66bcd-6692-4878-9112-a550c66d3fca';
        RAISE NOTICE 'Message (legacy) search: found %', message_count;
    ELSE
        RAISE NOTICE 'Message (legacy) table does not exist';
    END IF;
END $$;

-- 4. Show recent messages from Message_v2 to see the actual IDs
SELECT 'Recent Message_v2 IDs:' as info;
SELECT id, "chatId", role, "createdAt" 
FROM "Message_v2" 
ORDER BY "createdAt" DESC 
LIMIT 10;

-- 5. Check if there are any messages in legacy Message table
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Message' AND table_schema = 'public') THEN
        RAISE NOTICE 'Legacy Message table exists. Showing recent messages:';
        PERFORM 1; -- This will be replaced with actual query if table exists
    ELSE
        RAISE NOTICE 'No legacy Message table found';
    END IF;
END $$;

-- 6. Show which chat this missing message should belong to
-- Check if there are any chats that might contain this message
SELECT 'All chats with recent activity:' as info;
SELECT 
    c.id as chat_id, 
    c.title, 
    c."createdAt",
    COUNT(m.id) as message_count_in_v2
FROM "Chat" c
LEFT JOIN "Message_v2" m ON c.id = m."chatId"
GROUP BY c.id, c.title, c."createdAt"
ORDER BY c."createdAt" DESC
LIMIT 5;