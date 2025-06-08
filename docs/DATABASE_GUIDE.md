# 🗄️ PostgreSQL Database Guide for Telogical Chatbot

This guide provides comprehensive SQL commands and scripts for managing the Telogical Chatbot PostgreSQL database, including table inspection, data manipulation, troubleshooting, and maintenance.

## 📋 **Table of Contents**

1. [Database Schema Overview](#database-schema-overview)
2. [Quick Reference Commands](#quick-reference-commands)
3. [Table Inspection & Analysis](#table-inspection--analysis)
4. [Data Queries & Manipulation](#data-queries--manipulation)
5. [User Management](#user-management)
6. [Chat & Message Operations](#chat--message-operations)
7. [Database Maintenance](#database-maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Performance Optimization](#performance-optimization)

---

## 📊 **Database Schema Overview**

### **Core Tables**
| Table | Purpose | Key Relationships |
|-------|---------|------------------|
| `User` | User authentication & profiles | Primary table for all users |
| `Chat` | Conversation sessions | References `User.id` |
| `Message` | Individual chat messages | References `Chat.id` |
| `Document` | Uploaded files & documents | References `User.id` |
| `Vote` | Message feedback (thumbs up/down) | References `Chat.id` |
| `Suggestion` | AI suggestions for improvements | References `User.id`, `Document.id` |

### **Database Connection**
```bash
# Connect to your Azure PostgreSQL database
psql "postgres://username:password@host:5432/database_name?sslmode=require"

# Or using environment variables
psql $POSTGRES_URL
```

---

## ⚡ **Quick Reference Commands**

### **Essential Database Commands**
```sql
-- List all databases
\l

-- Connect to database
\c database_name

-- List all tables
\dt

-- Describe table structure
\d "TableName"

-- List all users/roles
\du

-- Show current database
SELECT current_database();

-- Show current user
SELECT current_user;

-- Exit psql
\q
```

---

## 🔍 **Table Inspection & Analysis**

### **Check All Tables and Their Structure**
```sql
-- List all tables in public schema
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Get detailed table structure with constraints
SELECT
    t.table_name,
    c.column_name,
    c.data_type,
    c.character_maximum_length,
    c.column_default,
    c.is_nullable,
    CASE
        WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY'
        WHEN fk.column_name IS NOT NULL THEN 'FOREIGN KEY'
        ELSE ''
    END as key_type
FROM information_schema.tables t
LEFT JOIN information_schema.columns c ON c.table_name = t.table_name
LEFT JOIN (
    SELECT ku.table_name, ku.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
    WHERE tc.constraint_type = 'PRIMARY KEY'
) pk ON pk.table_name = t.table_name AND pk.column_name = c.column_name
LEFT JOIN (
    SELECT ku.table_name, ku.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
) fk ON fk.table_name = t.table_name AND fk.column_name = c.column_name
WHERE t.table_schema = 'public'
ORDER BY t.table_name, c.ordinal_position;
```

### **Check Foreign Key Relationships**
```sql
-- View all foreign key constraints
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name;
```

### **Get Record Counts for All Tables**
```sql
-- Quick overview of data in all tables
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
```

---

## 👥 **User Management**

### **View All Users**
```sql
-- Check all users with basic information
SELECT
    id,
    email,
    name,
    image IS NOT NULL as has_image,
    password IS NOT NULL as has_password,
    "createdAt"
FROM "User"
ORDER BY "createdAt" DESC;
```

### **Create New User**
```sql
-- Create a new user (manual)
INSERT INTO "User" (id, email, name, "createdAt")
VALUES (
    gen_random_uuid(),
    'newuser@example.com',
    'New User Name',
    NOW()
);
```

### **Update User Information**
```sql
-- Update user name
UPDATE "User" 
SET name = 'Updated Name'
WHERE email = 'user@example.com';

-- Update user image
UPDATE "User" 
SET image = 'https://example.com/avatar.jpg'
WHERE id = 'user-id-here';
```

### **Find User by Email or ID**
```sql
-- Find user by email
SELECT * FROM "User" WHERE email = 'user@example.com';

-- Find user by ID
SELECT * FROM "User" WHERE id = 'specific-user-id';

-- Search users by name pattern
SELECT * FROM "User" WHERE name ILIKE '%search_term%';
```

### **Delete User (Careful!)**
```sql
-- Delete user and all related data (CASCADE)
DELETE FROM "User" WHERE email = 'user@example.com';

-- Check what would be deleted first
SELECT 
    u.email,
    COUNT(c.id) as chat_count,
    COUNT(d.id) as document_count
FROM "User" u
LEFT JOIN "Chat" c ON u.id = c."userId"
LEFT JOIN "Document" d ON u.id = d."userId"
WHERE u.email = 'user@example.com'
GROUP BY u.email;
```

---

## 💬 **Chat & Message Operations**

### **View Recent Chats**
```sql
-- Get recent chats with user information
SELECT
    c.id,
    c.title,
    c."createdAt",
    c.visibility,
    u.email,
    u.name,
    COUNT(m.id) as message_count
FROM "Chat" c
JOIN "User" u ON c."userId" = u.id
LEFT JOIN "Message" m ON c.id = m."chatId"
GROUP BY c.id, u.email, u.name
ORDER BY c."createdAt" DESC
LIMIT 10;
```

### **View Messages in a Chat**
```sql
-- Get all messages from a specific chat
SELECT
    m.id,
    m.role,
    m.content,
    m."createdAt",
    c.title as chat_title,
    u.email as user_email
FROM "Message" m
JOIN "Chat" c ON m."chatId" = c.id
JOIN "User" u ON c."userId" = u.id
WHERE c.id = 'chat-id-here'
ORDER BY m."createdAt" ASC;
```

### **Find Chats by Content**
```sql
-- Search for chats containing specific keywords
SELECT DISTINCT
    c.id,
    c.title,
    c."createdAt",
    u.email
FROM "Chat" c
JOIN "User" u ON c."userId" = u.id
JOIN "Message" m ON c.id = m."chatId"
WHERE m.content ILIKE '%search_keyword%'
ORDER BY c."createdAt" DESC;
```

### **Chat Statistics**
```sql
-- Get chat statistics by user
SELECT
    u.email,
    u.name,
    COUNT(c.id) as total_chats,
    COUNT(m.id) as total_messages,
    MAX(c."createdAt") as last_chat_date
FROM "User" u
LEFT JOIN "Chat" c ON u.id = c."userId"
LEFT JOIN "Message" m ON c.id = m."chatId"
GROUP BY u.id, u.email, u.name
ORDER BY total_chats DESC;
```

### **Delete Old Chats**
```sql
-- Delete chats older than 30 days (careful!)
DELETE FROM "Chat" 
WHERE "createdAt" < NOW() - INTERVAL '30 days';

-- Check what would be deleted first
SELECT COUNT(*) as chats_to_delete
FROM "Chat" 
WHERE "createdAt" < NOW() - INTERVAL '30 days';
```

---

## 🔧 **Database Maintenance**

### **Check Database Size**
```sql
-- Get database size
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE pg_database.datname = current_database();

-- Get table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;
```

### **Vacuum and Analyze**
```sql
-- Analyze all tables for query optimization
ANALYZE;

-- Vacuum specific table
VACUUM "User";

-- Full vacuum and analyze (use carefully in production)
VACUUM ANALYZE;
```

### **Check Index Usage**
```sql
-- View all indexes and their usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_tup_read DESC;
```

### **Backup Commands**
```bash
# Create database backup
pg_dump "$POSTGRES_URL" > backup_$(date +%Y%m%d_%H%M%S).sql

# Create compressed backup
pg_dump "$POSTGRES_URL" | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup specific tables only
pg_dump "$POSTGRES_URL" -t "User" -t "Chat" > user_chat_backup.sql

# Restore from backup
psql "$POSTGRES_URL" < backup_file.sql
```

---

## 🚨 **Troubleshooting**

### **Check for Orphaned Records**
```sql
-- Find chats with non-existent users
SELECT
    c.id as chat_id,
    c."userId" as user_id,
    c.title,
    u.email,
    CASE WHEN u.id IS NULL THEN 'ORPHANED' ELSE 'OK' END as status
FROM "Chat" c
LEFT JOIN "User" u ON c."userId" = u.id
WHERE u.id IS NULL;

-- Find messages with non-existent chats
SELECT
    m.id as message_id,
    m."chatId" as chat_id,
    c.title,
    CASE WHEN c.id IS NULL THEN 'ORPHANED' ELSE 'OK' END as status
FROM "Message" m
LEFT JOIN "Chat" c ON m."chatId" = c.id
WHERE c.id IS NULL;
```

### **Fix Orphaned Records**
```sql
-- Delete orphaned chats (no user)
DELETE FROM "Chat" 
WHERE "userId" NOT IN (SELECT id FROM "User");

-- Delete orphaned messages (no chat)
DELETE FROM "Message" 
WHERE "chatId" NOT IN (SELECT id FROM "Chat");
```

### **Check for Duplicate Users**
```sql
-- Find duplicate emails
SELECT 
    email, 
    COUNT(*) as count
FROM "User"
GROUP BY email
HAVING COUNT(*) > 1;

-- Find duplicate user IDs (shouldn't happen but check)
SELECT 
    id, 
    COUNT(*) as count
FROM "User"
GROUP BY id
HAVING COUNT(*) > 1;
```

### **Database Connection Issues**
```sql
-- Check current connections
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start
FROM pg_stat_activity
WHERE datname = current_database();

-- Kill specific connection (if needed)
-- SELECT pg_terminate_backend(pid) WHERE pid = 'problem_pid';
```

---

## 🚀 **Performance Optimization**

### **Create Missing Indexes**
```sql
-- Create indexes for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_email ON "User"(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_created_at ON "User"("createdAt");
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_user_id ON "Chat"("userId");
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_created_at ON "Chat"("createdAt");
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_message_chat_id ON "Message"("chatId");
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_message_created_at ON "Message"("createdAt");
```

### **Query Performance Analysis**
```sql
-- Enable timing
\timing

-- Explain query plan
EXPLAIN ANALYZE 
SELECT c.*, u.email 
FROM "Chat" c 
JOIN "User" u ON c."userId" = u.id 
ORDER BY c."createdAt" DESC 
LIMIT 10;

-- Check slow queries (if available)
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    min_time,
    max_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

---

## 📁 **Useful Scripts Reference**

The repository includes pre-written SQL scripts in `scripts/helpful_postgres/`:

| Script | Purpose |
|--------|---------|
| `check_all_tables.sql` | Inspect all tables and their structure |
| `check_all_users.sql` | View all users with basic information |
| `database_state.sql` | Complete database state overview |

### **How to Use the Scripts**
```bash
# Run a specific script
psql "$POSTGRES_URL" -f scripts/helpful_postgres/check_all_tables.sql

# Run script and save output
psql "$POSTGRES_URL" -f scripts/helpful_postgres/database_state.sql > database_report.txt
```

---

## 🔗 **Quick Actions Cheat Sheet**

```sql
-- Emergency: Find and fix authentication issues
SELECT id, email, password IS NOT NULL as has_password 
FROM "User" 
WHERE email = 'problematic-user@email.com';

-- Emergency: Clean up test data
DELETE FROM "Chat" WHERE title LIKE '%test%';
DELETE FROM "User" WHERE email LIKE '%test%';

-- Emergency: Reset user password (set to NULL for OAuth users)
UPDATE "User" SET password = NULL WHERE email = 'oauth-user@email.com';

-- Emergency: Check database integrity
SELECT 
    'Users' as table_name, COUNT(*) as count FROM "User"
UNION ALL
SELECT 
    'Chats' as table_name, COUNT(*) as count FROM "Chat"
UNION ALL
SELECT 
    'Messages' as table_name, COUNT(*) as count FROM "Message";
```

---

## ⚠️ **Safety Guidelines**

### **Before Making Changes:**
1. **Always backup** before major operations
2. **Test queries** with `SELECT` before `UPDATE`/`DELETE`
3. **Use transactions** for multi-step operations
4. **Check foreign key constraints** before deleting

### **Safe Operation Pattern:**
```sql
-- Start transaction
BEGIN;

-- Your operations here
UPDATE "User" SET name = 'New Name' WHERE id = 'specific-id';

-- Check results
SELECT * FROM "User" WHERE id = 'specific-id';

-- If everything looks good:
COMMIT;
-- If something's wrong:
-- ROLLBACK;
```

---

## 📞 **Need Help?**

- **Connection Issues**: Check `POSTGRES_URL` environment variable
- **Permission Issues**: Verify database user permissions
- **Performance Issues**: Run `ANALYZE` and check indexes
- **Data Issues**: Use the troubleshooting queries above

**Remember**: When in doubt, always backup first! 🔒