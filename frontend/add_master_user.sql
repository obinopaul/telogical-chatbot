-- SQL script to add a master user to the Telogical PostgreSQL database
-- Run this in your PostgreSQL database to create a test user

-- Master User Credentials:
-- Email: master@telogical.com
-- Password: TelogicalMaster123
-- Name: Master Admin User

-- The password hash is generated using the same method as the frontend:
-- SHA256(password + 'telogical-salt')
-- Password "TelogicalMaster123" becomes hash: d77f599ed8ab508114bfcd6ffeeef69122f54c1239daade578d6404950a04ec3

INSERT INTO "User" (
    id,
    email,
    password,
    name,
    "createdAt",
    "updatedAt"
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'master@telogical.com',
    'd77f599ed8ab508114bfcd6ffeeef69122f54c1239daade578d6404950a04ec3',
    'Master Admin User',
    NOW(),
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    password = EXCLUDED.password,
    name = EXCLUDED.name,
    "updatedAt" = NOW();

-- Verify the user was created
SELECT id, email, name, "createdAt" FROM "User" WHERE email = 'master@telogical.com';

-- Instructions for use:
-- 1. Connect to your PostgreSQL database
-- 2. Run this SQL script
-- 3. Use these credentials to test login:
--    Email: master@telogical.com
--    Password: TelogicalMaster123