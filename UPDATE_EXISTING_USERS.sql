-- Run this SQL after the migration to set types for existing users
-- This assumes users with passwords are 'credentials' and users without are 'regular' (OAuth)

UPDATE "User" 
SET type = CASE 
  WHEN password IS NOT NULL THEN 'credentials'::user_type
  ELSE 'regular'::user_type
END
WHERE type IS NULL;