-- Check current state and update existing users only
-- Run this to see what's in the User table:
SELECT id, email, type, CASE WHEN password IS NOT NULL THEN 'has_password' ELSE 'no_password' END as password_status 
FROM "User" 
LIMIT 5;

-- Update users that don't have type set properly:
UPDATE "User" 
SET type = CASE 
  WHEN password IS NOT NULL THEN 'credentials'::user_type
  ELSE 'regular'::user_type
END
WHERE type IS NULL;