-- Investigate the missing message and related chat data

-- 1. Find the chat that should contain this message
SELECT 'Looking for chat 7b240f5f-1dbe-4ec0-be81-042b9a244586:' as info;

-- 2. Check if this chat exists
SELECT 'Chat exists:' as check_type, 
       CASE WHEN EXISTS (SELECT 1 FROM "Chat" WHERE id = '7b240f5f-1dbe-4ec0-be81-042b9a244586') 
            THEN 'YES ✅' 
            ELSE 'NO ❌' 
       END as result;

-- 3. Show all messages in this chat from both tables
SELECT 'Messages in this chat from Message table:' as info;
SELECT id, role, "createdAt", 
       CASE WHEN LENGTH(parts::text) > 50 
            THEN LEFT(parts::text, 50) || '...' 
            ELSE parts::text 
       END as content_preview
FROM "Message" 
WHERE "chatId" = '7b240f5f-1dbe-4ec0-be81-042b9a244586'
ORDER BY "createdAt" DESC;

SELECT 'Messages in this chat from Message_v2 table:' as info;
SELECT id, role, "createdAt",
       CASE WHEN LENGTH(parts::text) > 50 
            THEN LEFT(parts::text, 50) || '...' 
            ELSE parts::text 
       END as content_preview
FROM "Message_v2" 
WHERE "chatId" = '7b240f5f-1dbe-4ec0-be81-042b9a244586'
ORDER BY "createdAt" DESC;

-- 4. Count total messages in this chat
SELECT 'Message counts for this chat:' as info;
SELECT 'Message table' as table_name, COUNT(*) as count
FROM "Message" 
WHERE "chatId" = '7b240f5f-1dbe-4ec0-be81-042b9a244586'
UNION ALL
SELECT 'Message_v2 table' as table_name, COUNT(*) as count
FROM "Message_v2" 
WHERE "chatId" = '7b240f5f-1dbe-4ec0-be81-042b9a244586';

-- 5. Check for any votes on this chat
SELECT 'Existing votes for this chat:' as info;
SELECT COUNT(*) as vote_count, 
       STRING_AGG(DISTINCT "messageId"::text, ', ') as voted_message_ids
FROM "Vote" 
WHERE "chatId" = '7b240f5f-1dbe-4ec0-be81-042b9a244586';

-- 6. Show most recent messages across all chats to understand the pattern
SELECT 'Most recent messages (last 10):' as info;
SELECT id, "chatId", role, "createdAt"
FROM "Message" 
ORDER BY "createdAt" DESC 
LIMIT 10;

-- 7. Emergency fix: Create a dummy message with the missing ID to allow voting
-- (Only if we want to allow voting on cached/phantom messages)
/*
INSERT INTO "Message" (id, "chatId", role, parts, attachments, "createdAt")
VALUES (
    '0adbfc84-80f4-4d22-a543-81933c0ed8b5',
    '7b240f5f-1dbe-4ec0-be81-042b9a244586', 
    'assistant',
    '[{"type": "text", "text": "[Recovered message - content may be incomplete]"}]'::json,
    '[]'::json,
    NOW()
) ON CONFLICT (id) DO NOTHING;
*/