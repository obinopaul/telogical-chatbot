-- Manual database update if drizzle-kit doesn't work
-- Connect to your PostgreSQL database and run these commands:

-- 1. Create the enum type
CREATE TYPE user_type AS ENUM ('regular', 'credentials');

-- 2. Add the column to the User table
ALTER TABLE "User" 
ADD COLUMN type user_type DEFAULT 'regular' NOT NULL;

-- 3. Update existing users based on whether they have passwords
UPDATE "User" 
SET type = CASE 
  WHEN password IS NOT NULL THEN 'credentials'::user_type
  ELSE 'regular'::user_type
END;