-- FIXED INVESTIGATION: Find the phantom message c7fe8f91-03d1-453b-872d-a089380a6db3

-- 1. Check phantom message in Message table (force result even if empty)
SELECT 
    'Phantom in Message table' as search_result,
    CASE 
        WHEN EXISTS (SELECT 1 FROM "Message" WHERE id = 'c7fe8f91-03d1-453b-872d-a089380a6db3') 
        THEN 'FOUND ⚠️' 
        ELSE 'NOT FOUND ✅' 
    END as status,
    COALESCE(
        (SELECT "chatId"::text FROM "Message" WHERE id = 'c7fe8f91-03d1-453b-872d-a089380a6db3'), 
        'N/A'
    ) as chat_id;

-- 2. Check phantom message in Message_v2 table
SELECT 
    'Phantom in Message_v2 table' as search_result,
    CASE 
        WHEN EXISTS (SELECT 1 FROM "Message_v2" WHERE id = 'c7fe8f91-03d1-453b-872d-a089380a6db3') 
        THEN 'FOUND ⚠️' 
        ELSE 'NOT FOUND ✅' 
    END as status,
    COALESCE(
        (SELECT "chatId"::text FROM "Message_v2" WHERE id = 'c7fe8f91-03d1-453b-872d-a089380a6db3'), 
        'N/A'
    ) as chat_id;

-- 3. Count messages in current chat bac149e6-1fe3-4ac2-ab4d-78d2af93cd67
SELECT 
    'Messages in current chat' as info,
    'Message table' as table_name,
    COUNT(*) as count,
    COALESCE(STRING_AGG(id::text, ', '), 'NONE') as message_ids
FROM "Message" 
WHERE "chatId" = 'bac149e6-1fe3-4ac2-ab4d-78d2af93cd67'

UNION ALL

SELECT 
    'Messages in current chat' as info,
    'Message_v2 table' as table_name,
    COUNT(*) as count,
    COALESCE(STRING_AGG(id::text, ', '), 'NONE') as message_ids
FROM "Message_v2" 
WHERE "chatId" = 'bac149e6-1fe3-4ac2-ab4d-78d2af93cd67';

-- 4. Check for manually created fake messages
SELECT 
    'Fake messages check' as info,
    table_name,
    COUNT(*) as fake_count
FROM (
    SELECT 'Message' as table_name FROM "Message" 
    WHERE LOWER(parts::text) LIKE '%recovered%' 
       OR LOWER(parts::text) LIKE '%phantom%' 
       OR LOWER(parts::text) LIKE '%cache%'
    UNION ALL
    SELECT 'Message_v2' as table_name FROM "Message_v2" 
    WHERE LOWER(parts::text) LIKE '%recovered%' 
       OR LOWER(parts::text) LIKE '%phantom%' 
       OR LOWER(parts::text) LIKE '%cache%'
) fake_search
GROUP BY table_name

UNION ALL

SELECT 'Fake messages check' as info, 'NONE FOUND', 0
WHERE NOT EXISTS (
    SELECT 1 FROM "Message" 
    WHERE LOWER(parts::text) LIKE '%recovered%' 
       OR LOWER(parts::text) LIKE '%phantom%' 
       OR LOWER(parts::text) LIKE '%cache%'
) AND NOT EXISTS (
    SELECT 1 FROM "Message_v2" 
    WHERE LOWER(parts::text) LIKE '%recovered%' 
       OR LOWER(parts::text) LIKE '%phantom%' 
       OR LOWER(parts::text) LIKE '%cache%'
);

-- 5. Check table existence
SELECT 
    'Table existence' as check_type,
    table_name,
    'EXISTS' as status
FROM information_schema.tables 
WHERE table_name IN ('Message', 'Message_v2') 
  AND table_schema = 'public';