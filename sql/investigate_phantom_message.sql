-- INVESTIGATE THE PHANTOM MESSAGE: c7fe8f91-03d1-453b-872d-a089380a6db3
-- Let's find out where this phantom message is coming from

-- 1. Check if phantom message exists in Message table
SELECT 'Phantom message in Message table:' as check_type;
SELECT id, "chatId", role, "createdAt", 
       CASE WHEN LENGTH(parts::text) > 50 
            THEN LEFT(parts::text, 50) || '...' 
            ELSE parts::text 
       END as content_preview
FROM "Message" 
WHERE id = 'c7fe8f91-03d1-453b-872d-a089380a6db3';

-- 2. Check if phantom message exists in Message_v2 table
SELECT 'Phantom message in Message_v2 table:' as check_type;
SELECT id, "chatId", role, "createdAt", 
       CASE WHEN LENGTH(parts::text) > 50 
            THEN LEFT(parts::text, 50) || '...' 
            ELSE parts::text 
       END as content_preview
FROM "Message_v2" 
WHERE id = 'c7fe8f91-03d1-453b-872d-a089380a6db3';

-- 3. Check ALL messages in the current chat (bac149e6-1fe3-4ac2-ab4d-78d2af93cd67)
SELECT 'ALL messages in current chat from Message table:' as info;
SELECT id, role, "createdAt", 
       CASE WHEN LENGTH(parts::text) > 50 
            THEN LEFT(parts::text, 50) || '...' 
            ELSE parts::text 
       END as content_preview
FROM "Message" 
WHERE "chatId" = 'bac149e6-1fe3-4ac2-ab4d-78d2af93cd67'
ORDER BY "createdAt";

SELECT 'ALL messages in current chat from Message_v2 table:' as info;
SELECT id, role, "createdAt", 
       CASE WHEN LENGTH(parts::text) > 50 
            THEN LEFT(parts::text, 50) || '...' 
            ELSE parts::text 
       END as content_preview
FROM "Message_v2" 
WHERE "chatId" = 'bac149e6-1fe3-4ac2-ab4d-78d2af93cd67'
ORDER BY "createdAt";

-- 4. Search for this phantom message ID across ALL chats in both tables
SELECT 'Phantom message search across ALL chats:' as info;
SELECT 'Message table' as table_name, id, "chatId", role, "createdAt"
FROM "Message" 
WHERE id = 'c7fe8f91-03d1-453b-872d-a089380a6db3'
UNION ALL
SELECT 'Message_v2 table' as table_name, id, "chatId", role, "createdAt"
FROM "Message_v2" 
WHERE id = 'c7fe8f91-03d1-453b-872d-a089380a6db3';

-- 5. Check if there are any manually created phantom messages
SELECT 'Manually created phantom messages (containing "recovered", "phantom", "cache"):' as info;
SELECT table_name, id, "chatId", role, parts::text as content
FROM (
    SELECT 'Message' as table_name, id, "chatId", role, parts FROM "Message"
    UNION ALL
    SELECT 'Message_v2' as table_name, id, "chatId", role, parts FROM "Message_v2"
) combined
WHERE LOWER(parts::text) LIKE '%recovered%' 
   OR LOWER(parts::text) LIKE '%phantom%' 
   OR LOWER(parts::text) LIKE '%cache%';

-- 6. Show the exact saved vs loaded mismatch
SELECT 'SAVED vs LOADED mismatch analysis:' as info;
SELECT 'SAVED USER MESSAGE' as type, 'edbc8cba-d376-441e-8338-895fb83e791a'::text as message_id
UNION ALL
SELECT 'SAVED ASSISTANT MESSAGE' as type, '4d246e0f-6559-4839-827e-5006880cf82e'::text as message_id
UNION ALL
SELECT 'PHANTOM VOTING MESSAGE' as type, 'c7fe8f91-03d1-453b-872d-a089380a6db3'::text as message_id;