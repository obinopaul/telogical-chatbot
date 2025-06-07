-- Check what's in the User table
SELECT
    id,
    email,
    name,
    image,
    password IS NOT NULL as has_password,
    created_at
FROM "User"
ORDER BY created_at DESC;

-- Check the Chat table
SELECT
    id,
    "createdAt",
    title,
    "userId",
    visibility
FROM "Chat"
ORDER BY "createdAt" DESC;

-- Check if the specific user causing the error exists
SELECT
    id,
    email,
    name,
    created_at
FROM "User"
WHERE id = 'a7ca2088-bf94-4f76-9bea-1d0d7c03fe54';

-- Get record counts for all tables
SELECT 'User' as table_name, count(*) as record_count FROM "User"
UNION ALL
SELECT 'Chat' as table_name, count(*) as record_count FROM "Chat"
UNION ALL
SELECT 'Message_v2' as table_name, count(*) as record_count FROM "Message_v2"
UNION ALL
SELECT 'Vote_v2' as table_name, count(*) as record_count FROM "Vote_v2"
UNION ALL
SELECT 'Document' as table_name, count(*) as record_count FROM "Document"
UNION ALL
SELECT 'Suggestion' as table_name, count(*) as record_count FROM "Suggestion"
UNION ALL
SELECT 'Stream' as table_name, count(*) as record_count FROM "Stream"
UNION ALL
SELECT 'QueryCache' as table_name, count(*) as record_count FROM "QueryCache";

-- Check for any orphaned chats (chats with non-existent users)
SELECT
    c.id as chat_id,
    c."userId" as user_id,
    c.title,
    u.email,
    CASE WHEN u.id IS NULL THEN 'ORPHANED' ELSE 'OK' END as status
FROM "Chat" c
LEFT JOIN "User" u ON c."userId" = u.id
ORDER BY c."createdAt" DESC;
