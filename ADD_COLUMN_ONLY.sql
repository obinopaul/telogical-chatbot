-- Skip enum creation since it already exists
-- Just add the column to the User table

-- Add the type column to the User table
ALTER TABLE "User" 
ADD COLUMN type user_type DEFAULT 'regular' NOT NULL;

-- Update existing users based on whether they have passwords
UPDATE "User" 
SET type = CASE 
  WHEN password IS NOT NULL THEN 'credentials'::user_type
  ELSE 'regular'::user_type
END;