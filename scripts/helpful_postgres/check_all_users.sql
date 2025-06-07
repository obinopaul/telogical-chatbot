-- Check all users in the User table
SELECT
    id,
    email,
    name,
    image IS NOT NULL as has_image,
    password IS NOT NULL as has_password,
    created_at
FROM "User"
ORDER BY created_at DESC;