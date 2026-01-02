-- Migration: PA Reports Storage Bucket Policies
-- Date: 2026-01-01
-- Description: Creates RLS policies for the pa-reports storage bucket
-- Prerequisite: The 'pa-reports' bucket must exist in Supabase Storage

-- ============================================================================
-- STORAGE POLICIES FOR pa-reports BUCKET
-- ============================================================================

-- 1. Allow authenticated users to upload files to pa-reports bucket
CREATE POLICY "Authenticated users can upload PA reports"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'pa-reports');

-- 2. Allow authenticated users to read/download files from pa-reports bucket
CREATE POLICY "Authenticated users can read PA reports"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'pa-reports');

-- 3. Allow service role full access (for backend operations)
CREATE POLICY "Service role has full access to PA reports"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'pa-reports')
WITH CHECK (bucket_id = 'pa-reports');

-- 4. Allow authenticated users to update their uploads (for upsert operations)
CREATE POLICY "Authenticated users can update PA reports"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'pa-reports')
WITH CHECK (bucket_id = 'pa-reports');

-- 5. Allow authenticated users to delete their uploads (optional cleanup)
CREATE POLICY "Authenticated users can delete PA reports"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'pa-reports');
