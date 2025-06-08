-- TEMPORARY FIX: Handle phantom/cached messages
-- This creates placeholder entries for messages that exist in cache but not in database

-- Create the missing message as a placeholder
INSERT INTO "Message" (id, "chatId", role, parts, attachments, "createdAt")
VALUES (
    '0adbfc84-80f4-4d22-a543-81933c0ed8b5',
    '7b240f5f-1dbe-4ec0-be81-042b9a244586', 
    'assistant',
    '[{"type": "text", "text": "[Message recovered from cache - please refresh the page for accurate content]"}]'::json,
    '[]'::json,
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- Verify the fix
SELECT 'Phantom message fix:' as status;
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM "Message" WHERE id = '0adbfc84-80f4-4d22-a543-81933c0ed8b5') 
        THEN 'Message now exists - voting should work ✅'
        ELSE 'Fix failed ❌'
    END as result;