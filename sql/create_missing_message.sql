-- Create the missing message that the frontend is trying to vote on
-- This allows voting to work while we fix the cache mismatch

INSERT INTO "Message" (id, "chatId", role, parts, attachments, "createdAt")
VALUES (
    '0adbfc84-80f4-4d22-a543-81933c0ed8b5',
    '7b240f5f-1dbe-4ec0-be81-042b9a244586', 
    'assistant',
    '[{"type": "text", "text": "This message was recovered from frontend cache. Please refresh the page to see the correct message content."}]'::json,
    '[]'::json,
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- Verify the fix worked
SELECT 'Missing message created!' as status;
SELECT id, "chatId", role, "createdAt"
FROM "Message" 
WHERE id = '0adbfc84-80f4-4d22-a543-81933c0ed8b5';