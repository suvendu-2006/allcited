-- Verification script for STEP 25 Done when gate:
-- "a Supabase-side test insert as user A is invisible to user B."

BEGIN;

-- 1. Simulate User Alice ('user_alice_123')
SET LOCAL ROLE authenticated;
SET LOCAL "request.jwt.claims" = '{"sub": "user_alice_123", "role": "authenticated"}';

-- Insert document as Alice
INSERT INTO saved_documents (id, user_id, filename, format, file_size_bytes, doc_hash)
VALUES ('00000000-0000-0000-0000-000000000001', 'user_alice_123', 'alice_confidential.pdf', 'pdf', 1024, 'hash_alice_1');

-- Alice can see her document
SELECT count(*) AS alice_doc_count FROM saved_documents WHERE user_id = 'user_alice_123';
-- Expected: 1

-- 2. Simulate User Bob ('user_bob_456')
SET LOCAL "request.jwt.claims" = '{"sub": "user_bob_456", "role": "authenticated"}';

-- Bob queries saved_documents (must return 0 rows due to RLS)
SELECT count(*) AS bob_sees_alice_docs FROM saved_documents WHERE user_id = 'user_alice_123';
-- Expected: 0

-- Bob tries to SELECT all saved_documents
SELECT count(*) AS bob_total_visible FROM saved_documents;
-- Expected: 0

-- Bob attempts to delete Alice's document (should affect 0 rows)
DELETE FROM saved_documents WHERE id = '00000000-0000-0000-0000-000000000001';

-- Switch back to Alice to ensure her document was NOT deleted
SET LOCAL "request.jwt.claims" = '{"sub": "user_alice_123", "role": "authenticated"}';
SELECT count(*) AS alice_doc_still_exists FROM saved_documents WHERE id = '00000000-0000-0000-0000-000000000001';
-- Expected: 1

ROLLBACK;
