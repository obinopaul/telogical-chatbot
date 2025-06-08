-- Telogical Chatbot Database Quick Reference
-- This script combines the most useful database queries for daily operations
-- Run sections individually as needed

-- =================================================================
-- SECTION 1: DATABASE OVERVIEW
-- =================================================================

-- Quick database state check
SELECT 'Database State Check' as info, current_database() as database_name, current_user as connected_user;

-- Table record counts
SELECT 'User' as table_name, count(*) as record_count FROM "User"
UNION ALL
SELECT 'Chat' as table_name, count(*) as record_count FROM "Chat"
UNION ALL
SELECT 'Message' as table_name, count(*) as record_count FROM "Message"
UNION ALL
SELECT 'Document' as table_name, count(*) as record_count FROM "Document"
UNION ALL
SELECT 'Vote' as table_name, count(*) as record_count FROM "Vote"
UNION ALL
SELECT 'Suggestion' as table_name, count(*) as record_count FROM "Suggestion"
ORDER BY table_name;

-- =================================================================
-- SECTION 2: USER MANAGEMENT
-- =================================================================

-- Recent users (last 10)
SELECT
    id,
    email,
    name,
    image IS NOT NULL as has_image,
    password IS NOT NULL as has_password,
    "createdAt"
FROM "User"
ORDER BY "createdAt" DESC
LIMIT 10;

-- =================================================================
-- SECTION 3: CHAT ACTIVITY
-- =================================================================

-- Recent chats with user info
SELECT
    c.id as chat_id,
    c.title,
    c."createdAt",
    c.visibility,
    u.email,
    u.name as user_name,
    COUNT(m.id) as message_count
FROM "Chat" c
JOIN "User" u ON c."userId" = u.id
LEFT JOIN "Message" m ON c.id = m."chatId"
GROUP BY c.id, u.email, u.name
ORDER BY c."createdAt" DESC
LIMIT 10;

-- =================================================================
-- SECTION 4: SYSTEM HEALTH CHECKS
-- =================================================================

-- Check for orphaned chats (chats with non-existent users)
SELECT
    c.id as chat_id,
    c."userId" as user_id,
    c.title,
    u.email,
    CASE WHEN u.id IS NULL THEN 'ORPHANED ⚠️' ELSE 'OK ✅' END as status
FROM "Chat" c
LEFT JOIN "User" u ON c."userId" = u.id
WHERE u.id IS NULL;

-- Check for duplicate emails (should be none)
SELECT 
    email, 
    COUNT(*) as count,
    CASE WHEN COUNT(*) > 1 THEN 'DUPLICATE ⚠️' ELSE 'OK ✅' END as status
FROM "User"
GROUP BY email
HAVING COUNT(*) > 1;

-- =================================================================
-- SECTION 5: AUTHENTICATION DEBUGGING
-- =================================================================

-- Users with authentication method breakdown
SELECT
    CASE 
        WHEN password IS NOT NULL THEN 'Credentials Auth'
        WHEN password IS NULL AND image IS NOT NULL THEN 'OAuth (Google)'
        ELSE 'Unknown'
    END as auth_method,
    COUNT(*) as user_count
FROM "User"
GROUP BY 
    CASE 
        WHEN password IS NOT NULL THEN 'Credentials Auth'
        WHEN password IS NULL AND image IS NOT NULL THEN 'OAuth (Google)'
        ELSE 'Unknown'
    END;

-- =================================================================
-- SECTION 6: PERFORMANCE OVERVIEW
-- =================================================================

-- Database size overview
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Current database connections
SELECT 
    COUNT(*) as active_connections,
    COUNT(CASE WHEN state = 'active' THEN 1 END) as active_queries
FROM pg_stat_activity
WHERE datname = current_database();

-- =================================================================
-- SECTION 7: RECENT ACTIVITY SUMMARY
-- =================================================================

-- Activity summary for the last 24 hours
SELECT
    'Users created today' as metric,
    COUNT(*) as count
FROM "User"
WHERE "createdAt" > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'Chats created today' as metric,
    COUNT(*) as count
FROM "Chat"
WHERE "createdAt" > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'Messages sent today' as metric,
    COUNT(*) as count
FROM "Message"
WHERE "createdAt" > NOW() - INTERVAL '24 hours';

-- =================================================================
-- QUICK ACTIONS (UNCOMMENT AND MODIFY AS NEEDED)
-- =================================================================

-- Find specific user by email:
-- SELECT * FROM "User" WHERE email = 'user@example.com';

-- Find specific chat by ID:
-- SELECT * FROM "Chat" WHERE id = 'chat-id-here';

-- View messages in a specific chat:
-- SELECT role, content, "createdAt" FROM "Message" WHERE "chatId" = 'chat-id-here' ORDER BY "createdAt";

-- Delete test users (BE CAREFUL!):
-- DELETE FROM "User" WHERE email LIKE '%test%';

-- Clean up old chats (BE CAREFUL!):
-- DELETE FROM "Chat" WHERE "createdAt" < NOW() - INTERVAL '90 days';

SELECT 'Quick Reference Complete ✅' as status;