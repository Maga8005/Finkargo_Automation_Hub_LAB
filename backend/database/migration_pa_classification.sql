-- Migration: Add PA (Patrimonio Autónomo) Classification tables
-- Date: 2024-12-29
-- Description: Creates tables for PA Report Classification feature
-- Tables: pa_account_catalog, pa_classification_rules, pa_clasificacion_cuenta_rules,
--         pa_nexo_rules, pa_processing_history

-- ============================================================================
-- TABLE: pa_account_catalog
-- ============================================================================
-- Stores PA account mappings for filtering and homologation

CREATE TABLE IF NOT EXISTS pa_account_catalog (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Account identification (from Finkargo/NetSuite)
    cuenta_finkargo VARCHAR(50) NOT NULL,

    -- Homologation mapping
    cuenta_homologacion VARCHAR(50) NOT NULL,
    nombre_homologacion VARCHAR(255) NOT NULL,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),

    -- Ensure unique account numbers
    CONSTRAINT uq_pa_catalog_cuenta UNIQUE (cuenta_finkargo)
);

-- Index for fast lookups
CREATE INDEX idx_pa_catalog_cuenta ON pa_account_catalog(cuenta_finkargo);

-- ============================================================================
-- TABLE: pa_classification_rules
-- ============================================================================
-- Main classification rules: tipo_transaccion + tipo_comprobante -> categoria

CREATE TABLE IF NOT EXISTS pa_classification_rules (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Matching criteria
    tipo_transaccion VARCHAR(100) NOT NULL,
    tipo_comprobante VARCHAR(100) NOT NULL,

    -- Special matching (optional - for document number patterns)
    numero_documento_patron VARCHAR(50),  -- e.g., 'GBA%', 'PPR%', 'TBA%'

    -- Classification output
    categoria VARCHAR(100) NOT NULL,
    subcategoria_base VARCHAR(100),  -- Base subcategoria (may be modified by date logic)
    clasificacion_default VARCHAR(100),  -- Default clasificacion if no cuenta rule matches

    -- Priority for rule matching (lower = higher priority)
    prioridad INTEGER DEFAULT 100,

    -- Active flag
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),

    -- Composite unique constraint
    CONSTRAINT uq_pa_classification_rule UNIQUE (tipo_transaccion, tipo_comprobante, numero_documento_patron)
);

-- Indexes for fast matching
CREATE INDEX idx_pa_class_tipo_trans ON pa_classification_rules(tipo_transaccion);
CREATE INDEX idx_pa_class_tipo_comp ON pa_classification_rules(tipo_comprobante);
CREATE INDEX idx_pa_class_prioridad ON pa_classification_rules(prioridad);

-- ============================================================================
-- TABLE: pa_clasificacion_cuenta_rules
-- ============================================================================
-- Account name pattern -> clasificacion rules

CREATE TABLE IF NOT EXISTS pa_clasificacion_cuenta_rules (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern matching (e.g., 'Cartera%', '%Mora%', '%Fiduciarios%')
    cuenta_nombre_patron VARCHAR(255) NOT NULL,

    -- Classification output
    clasificacion VARCHAR(100) NOT NULL,

    -- Optional: restrict to specific category
    categoria_aplicable VARCHAR(100),

    -- Priority for rule matching (lower = higher priority)
    prioridad INTEGER DEFAULT 100,

    -- Active flag
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Index for pattern matching
CREATE INDEX idx_pa_clasif_cuenta_patron ON pa_clasificacion_cuenta_rules(cuenta_nombre_patron);

-- ============================================================================
-- TABLE: pa_nexo_rules
-- ============================================================================
-- Account name pattern -> nexo value rules

CREATE TABLE IF NOT EXISTS pa_nexo_rules (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern matching
    cuenta_nombre_patron VARCHAR(255) NOT NULL,

    -- Nexo output (typically "1", "2", "3", "4", "13")
    nexo VARCHAR(10) NOT NULL,

    -- Priority for rule matching (lower = higher priority)
    prioridad INTEGER DEFAULT 100,

    -- Active flag
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Index for pattern matching
CREATE INDEX idx_pa_nexo_patron ON pa_nexo_rules(cuenta_nombre_patron);

-- ============================================================================
-- TABLE: pa_processing_history
-- ============================================================================
-- Tracks all PA report processing sessions

CREATE TABLE IF NOT EXISTS pa_processing_history (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Session identification
    session_id VARCHAR(100) UNIQUE NOT NULL,  -- Format: PA-YYYYMMDD-HHMMSS-XXXX

    -- Processing status
    status VARCHAR(50) NOT NULL DEFAULT 'uploading'
        CHECK (status IN ('uploading', 'cleaning', 'cleaned', 'classifying', 'classified', 'failed')),

    -- File information
    original_filename VARCHAR(255),
    original_file_size BIGINT,

    -- Statistics (JSONB for flexibility)
    stats JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Example: {
    --   "total_rows": 50000,
    --   "pa_rows": 15000,
    --   "debito_sum": 1000000.00,
    --   "credito_sum": 1000000.00,
    --   "balance_valid": true,
    --   "classified_count": 14500,
    --   "unclassified_count": 500
    -- }

    -- File URLs (for download)
    cleaned_file_url TEXT,
    classified_file_url TEXT,

    -- Error tracking
    error_message TEXT,

    -- User tracking
    processed_by UUID REFERENCES auth.users(id),
    processed_by_email VARCHAR(255),

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cleaned_at TIMESTAMP WITH TIME ZONE,
    classified_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for history queries
CREATE INDEX idx_pa_history_session ON pa_processing_history(session_id);
CREATE INDEX idx_pa_history_status ON pa_processing_history(status);
CREATE INDEX idx_pa_history_date ON pa_processing_history(started_at DESC);
CREATE INDEX idx_pa_history_user ON pa_processing_history(processed_by);

-- ============================================================================
-- SEQUENCE for session_id generation
-- ============================================================================

CREATE SEQUENCE IF NOT EXISTS pa_session_seq START 1;

-- ============================================================================
-- FUNCTION to generate session_id
-- ============================================================================

CREATE OR REPLACE FUNCTION generate_pa_session_id()
RETURNS VARCHAR(100) AS $$
DECLARE
    v_timestamp VARCHAR(15);
    v_seq INTEGER;
    v_session_id VARCHAR(100);
BEGIN
    v_timestamp := TO_CHAR(NOW(), 'YYYYMMDD-HH24MISS');
    v_seq := NEXTVAL('pa_session_seq');
    v_session_id := 'PA-' || v_timestamp || '-' || LPAD(v_seq::TEXT, 4, '0');
    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER to auto-update updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_pa_tables_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for each table
CREATE TRIGGER trigger_pa_catalog_updated_at
    BEFORE UPDATE ON pa_account_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_pa_tables_updated_at();

CREATE TRIGGER trigger_pa_classification_updated_at
    BEFORE UPDATE ON pa_classification_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_pa_tables_updated_at();

CREATE TRIGGER trigger_pa_clasificacion_cuenta_updated_at
    BEFORE UPDATE ON pa_clasificacion_cuenta_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_pa_tables_updated_at();

CREATE TRIGGER trigger_pa_nexo_updated_at
    BEFORE UPDATE ON pa_nexo_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_pa_tables_updated_at();

CREATE TRIGGER trigger_pa_history_updated_at
    BEFORE UPDATE ON pa_processing_history
    FOR EACH ROW
    EXECUTE FUNCTION update_pa_tables_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE pa_account_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE pa_classification_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE pa_clasificacion_cuenta_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE pa_nexo_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE pa_processing_history ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read all rules
CREATE POLICY "Authenticated users can read pa_account_catalog"
ON pa_account_catalog FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Authenticated users can read pa_classification_rules"
ON pa_classification_rules FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Authenticated users can read pa_clasificacion_cuenta_rules"
ON pa_clasificacion_cuenta_rules FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Authenticated users can read pa_nexo_rules"
ON pa_nexo_rules FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Authenticated users can read pa_processing_history"
ON pa_processing_history FOR SELECT
TO authenticated
USING (true);

-- Policy: Authenticated users can insert/update (backend validates roles)
CREATE POLICY "Authenticated users can manage pa_account_catalog"
ON pa_account_catalog FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can manage pa_classification_rules"
ON pa_classification_rules FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can manage pa_clasificacion_cuenta_rules"
ON pa_clasificacion_cuenta_rules FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can manage pa_nexo_rules"
ON pa_nexo_rules FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can manage pa_processing_history"
ON pa_processing_history FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Policy: Service role has full access
CREATE POLICY "Service role has full access to pa_account_catalog"
ON pa_account_catalog FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role has full access to pa_classification_rules"
ON pa_classification_rules FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role has full access to pa_clasificacion_cuenta_rules"
ON pa_clasificacion_cuenta_rules FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role has full access to pa_nexo_rules"
ON pa_nexo_rules FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role has full access to pa_processing_history"
ON pa_processing_history FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE pa_account_catalog IS 'PA account catalog for filtering NetSuite data and homologation mapping';
COMMENT ON TABLE pa_classification_rules IS 'Main classification rules: tipo_transaccion + tipo_comprobante -> categoria';
COMMENT ON TABLE pa_clasificacion_cuenta_rules IS 'Account name pattern -> clasificacion rules';
COMMENT ON TABLE pa_nexo_rules IS 'Account name pattern -> nexo value rules';
COMMENT ON TABLE pa_processing_history IS 'Tracks all PA report processing sessions';

COMMENT ON COLUMN pa_account_catalog.cuenta_finkargo IS 'Account number from Finkargo/NetSuite';
COMMENT ON COLUMN pa_account_catalog.cuenta_homologacion IS 'Homologated account number for PA reporting';
COMMENT ON COLUMN pa_account_catalog.nombre_homologacion IS 'Homologated account name for PA reporting';

COMMENT ON COLUMN pa_classification_rules.tipo_transaccion IS 'Transaction type (e.g., Asiento, Factura de venta)';
COMMENT ON COLUMN pa_classification_rules.tipo_comprobante IS 'Document type (e.g., Ajustes Contables, Provisión Ingresos)';
COMMENT ON COLUMN pa_classification_rules.numero_documento_patron IS 'Optional pattern for document number matching (SQL LIKE syntax)';
COMMENT ON COLUMN pa_classification_rules.categoria IS 'Output category for matching transactions';
COMMENT ON COLUMN pa_classification_rules.subcategoria_base IS 'Base subcategory (may be modified by date logic)';

COMMENT ON COLUMN pa_clasificacion_cuenta_rules.cuenta_nombre_patron IS 'SQL LIKE pattern for account name matching';
COMMENT ON COLUMN pa_clasificacion_cuenta_rules.clasificacion IS 'Output classification value';
COMMENT ON COLUMN pa_clasificacion_cuenta_rules.categoria_aplicable IS 'Optional: only apply to this category';

COMMENT ON COLUMN pa_nexo_rules.cuenta_nombre_patron IS 'SQL LIKE pattern for account name matching';
COMMENT ON COLUMN pa_nexo_rules.nexo IS 'Output nexo value (e.g., 1, 2, 3, 4, 13)';

COMMENT ON COLUMN pa_processing_history.session_id IS 'Unique session identifier: PA-YYYYMMDD-HHMMSS-NNNN';
COMMENT ON COLUMN pa_processing_history.stats IS 'JSON object with processing statistics';
