-- Migration: Add missing contract template fields to clients table
-- Date: 2025-10-05
-- Description: Adds fields for complete contract template population

-- Add new columns to clients table
ALTER TABLE clients
ADD COLUMN IF NOT EXISTS direccion_comercial TEXT,
ADD COLUMN IF NOT EXISTS tipo_identificacion_representante VARCHAR(10) DEFAULT 'CC',
ADD COLUMN IF NOT EXISTS nombre_contrato_marco VARCHAR(100) DEFAULT 'Compra de Cartera',
ADD COLUMN IF NOT EXISTS kam_nombre VARCHAR(100),
ADD COLUMN IF NOT EXISTS kam_email VARCHAR(100),
ADD COLUMN IF NOT EXISTS destinatario_nombre VARCHAR(100),
ADD COLUMN IF NOT EXISTS destinatario_email VARCHAR(100);

-- Add comments to document the new fields
COMMENT ON COLUMN clients.direccion_comercial IS 'Full business address where importer conducts commercial activities';
COMMENT ON COLUMN clients.tipo_identificacion_representante IS 'Legal representative ID type: CC (Cédula de Ciudadanía), NIT, CE (Cédula de Extranjería), etc.';
COMMENT ON COLUMN clients.nombre_contrato_marco IS 'Framework contract name (e.g., Compra de Cartera, Factoring, etc.)';
COMMENT ON COLUMN clients.kam_nombre IS 'Key Account Manager full name';
COMMENT ON COLUMN clients.kam_email IS 'Key Account Manager email address';
COMMENT ON COLUMN clients.destinatario_nombre IS 'Notification recipient name (may differ from KAM)';
COMMENT ON COLUMN clients.destinatario_email IS 'Notification recipient email (may differ from KAM email)';

-- Update existing records with default values where NULL
UPDATE clients
SET
    tipo_identificacion_representante = 'CC'
WHERE tipo_identificacion_representante IS NULL;

UPDATE clients
SET
    nombre_contrato_marco = 'Compra de Cartera'
WHERE nombre_contrato_marco IS NULL;

-- Add index on email fields for faster lookups
CREATE INDEX IF NOT EXISTS idx_clients_kam_email ON clients(kam_email);
CREATE INDEX IF NOT EXISTS idx_clients_destinatario_email ON clients(destinatario_email);
