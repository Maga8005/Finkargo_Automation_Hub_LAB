-- Migration: Add Drive File Cache Table
-- Purpose: Cache Google Drive file IDs to avoid expensive search operations
-- Date: 2025-12-05

-- Create table to cache Drive file IDs by UUID
CREATE TABLE IF NOT EXISTS drive_file_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    uuid VARCHAR(100) NOT NULL,           -- UUID del documento (factura)
    file_type VARCHAR(10) NOT NULL,       -- 'pdf' o 'xml'
    drive_file_id VARCHAR(100) NOT NULL,  -- ID del archivo en Google Drive
    drive_file_name VARCHAR(255),         -- Nombre del archivo en Drive
    country VARCHAR(10) DEFAULT 'MX',     -- País ('MX' o 'CO')
    file_size_bytes INTEGER,              -- Tamaño del archivo (opcional)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: un UUID solo puede tener un PDF y un XML
    CONSTRAINT unique_uuid_file_type UNIQUE (uuid, file_type, country)
);

-- Index for fast lookups by UUID
CREATE INDEX IF NOT EXISTS idx_drive_file_cache_uuid ON drive_file_cache(uuid);

-- Index for country-specific queries
CREATE INDEX IF NOT EXISTS idx_drive_file_cache_country ON drive_file_cache(country);

-- Index for cleanup of old entries
CREATE INDEX IF NOT EXISTS idx_drive_file_cache_last_accessed ON drive_file_cache(last_accessed_at);

-- Enable RLS
ALTER TABLE drive_file_cache ENABLE ROW LEVEL SECURITY;

-- Policy: Service role can do everything
CREATE POLICY "Service role full access on drive_file_cache"
ON drive_file_cache
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Policy: Authenticated users can read
CREATE POLICY "Authenticated users can read drive_file_cache"
ON drive_file_cache
FOR SELECT
TO authenticated
USING (true);

-- Function to update last_accessed_at timestamp
CREATE OR REPLACE FUNCTION update_drive_cache_accessed()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update last_accessed_at on access (when updated_at changes)
DROP TRIGGER IF EXISTS trigger_update_drive_cache_accessed ON drive_file_cache;
CREATE TRIGGER trigger_update_drive_cache_accessed
    BEFORE UPDATE ON drive_file_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_drive_cache_accessed();

-- Comment on table
COMMENT ON TABLE drive_file_cache IS 'Cache de IDs de archivos de Google Drive para evitar búsquedas costosas por nombre';
COMMENT ON COLUMN drive_file_cache.uuid IS 'UUID del documento de facturación';
COMMENT ON COLUMN drive_file_cache.file_type IS 'Tipo de archivo: pdf o xml';
COMMENT ON COLUMN drive_file_cache.drive_file_id IS 'ID del archivo en Google Drive para descarga directa';
