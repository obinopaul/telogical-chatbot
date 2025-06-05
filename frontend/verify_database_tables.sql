-- ============================================
-- SQL Commands to Verify Database Tables
-- Run these in your pgAdmin desktop app
-- ============================================

-- 1. CHECK ALL TABLES IN YOUR DATABASE
-- This will show you every table that exists
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- 2. CHECK IF "User" TABLE EXISTS SPECIFICALLY
-- This should return 1 row if the table exists, 0 if it doesn't
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'User' 
    AND table_schema = 'public'
ORDER BY ordinal_position;

-- 3. CHECK USERS IN THE "User" TABLE
-- This will show all users currently stored
SELECT 
    id,
    email,
    name,
    created_at,
    CASE 
        WHEN password IS NOT NULL THEN 'Has Password' 
        ELSE 'No Password (OAuth User)' 
    END as password_status
FROM "User"
ORDER BY created_at DESC
LIMIT 10;

-- 4. CHECK FOR MASTER USER SPECIFICALLY
-- This should show the master user we created
SELECT 
    id,
    email,
    name,
    created_at,
    LENGTH(password) as password_length
FROM "User" 
WHERE email = 'master@telogical.com';

-- 5. COUNT TOTAL USERS
-- This shows how many users you have
SELECT 
    COUNT(*) as total_users,
    COUNT(password) as users_with_password,
    COUNT(*) - COUNT(password) as oauth_only_users
FROM "User";

-- ============================================
-- EXPECTED RESULTS:
-- ============================================
-- Query 1: Should show tables like "User", "Chat", "Message_v2", etc.
-- Query 2: Should show columns like id, email, password, name, image, created_at
-- Query 3: Should show your existing users including master@telogical.com
-- Query 4: Should show 1 row with master user details
-- Query 5: Should show user counts
-- ============================================