-- Debug the current state to find the missing message

-- 1. Check if the specific missing message exists anywhere
SELECT 'Searching for message: 0adbfc84-80f4-4d22-a543-81933c0ed8b5' as info;

-- 2. Check in Message table
SELECT 'Message table' as location, COUNT(*) as found
FROM "Message" 
WHERE id = '0adbfc84-80f4-4d22-a543-81933c0ed8b5';

-- 3. Check in Message_v2 table  
SELECT 'Message_v2 table' as location, COUNT(*) as found
FROM "Message_v2" 
WHERE id = '0adbfc84-80f4-4d22-a543-81933c0ed8b5';

-- 4. Show recent messages in both tables
SELECT 'Recent messages in Message table:' as info;
SELECT id, "chatId", role, "createdAt" 
FROM "Message" 
ORDER BY "createdAt" DESC 
LIMIT 5;

SELECT 'Recent messages in Message_v2 table:' as info;
SELECT id, "chatId", role, "createdAt" 
FROM "Message_v2" 
ORDER BY "createdAt" DESC 
LIMIT 5;

-- 5. Check total counts in both tables
SELECT 'Message table count' as table_name, COUNT(*) as total FROM "Message"
UNION ALL
SELECT 'Message_v2 table count' as table_name, COUNT(*) as total FROM "Message_v2";

-- 6. Check if there are any messages in Message_v2 that are NOT in Message
SELECT 'Messages in Message_v2 but NOT in Message:' as info;
SELECT COUNT(*) as missing_count
FROM "Message_v2" mv2
WHERE NOT EXISTS (
    SELECT 1 FROM "Message" m WHERE m.id = mv2.id
);