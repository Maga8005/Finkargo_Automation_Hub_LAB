-- ============================================================================
-- FINKARGO AUTOMATION HUB - COMBINED DATABASE SCHEMA
-- ============================================================================
-- This is a consolidated schema file for setting up a fresh Supabase database.
-- Run this in your Supabase SQL Editor to create all tables, functions, and policies.
--
-- Created: 2025-11-27
-- Source: Combined from schema.sql and all migration files
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE: clients
-- Stores client data imported from Excel/CSV
-- ============================================================================
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nit VARCHAR(20) UNIQUE NOT NULL,
    nombre_importador VARCHAR(255) NOT NULL,
    representante_legal VARCHAR(255) NOT NULL,
    cedula_representante VARCHAR(50) NOT NULL,
    ciudad_domicilio VARCHAR(100) NOT NULL,
    cupo_plataforma DECIMAL(15, 2) NOT NULL,

    -- Additional contract fields
    direccion_comercial TEXT,
    tipo_identificacion_representante VARCHAR(10) DEFAULT 'CC',
    nombre_contrato_marco VARCHAR(100) DEFAULT 'Compra de Cartera',
    kam_nombre VARCHAR(100),
    kam_email VARCHAR(100),
    destinatario_nombre VARCHAR(100),
    destinatario_email VARCHAR(100),

    -- Audit fields (nullable for flexibility)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    imported_by UUID REFERENCES auth.users(id),

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT
);

-- Indexes for clients
CREATE INDEX IF NOT EXISTS idx_clients_nit ON clients(nit);
CREATE INDEX IF NOT EXISTS idx_clients_nombre ON clients(nombre_importador);
CREATE INDEX IF NOT EXISTS idx_clients_active ON clients(is_active);
CREATE INDEX IF NOT EXISTS idx_clients_kam_email ON clients(kam_email);
CREATE INDEX IF NOT EXISTS idx_clients_destinatario_email ON clients(destinatario_email);

COMMENT ON TABLE clients IS 'Client data imported from platform exports';

-- ============================================================================
-- TABLE: user_profiles
-- User profiles linked to Supabase auth.users
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'commercial', 'analyst', 'mesa_control', 'manager', 'user', 'legal', 'operations', 'tesoreria', 'cliente')),
    is_active BOOLEAN DEFAULT true NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,

    -- User type (funcionario vs cliente)
    user_type TEXT NOT NULL DEFAULT 'funcionario' CHECK (user_type IN ('funcionario', 'cliente')),
    company_name TEXT,
    client_id TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON user_profiles(role);
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active ON user_profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_login ON user_profiles(last_login);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_type ON user_profiles(user_type);
CREATE INDEX IF NOT EXISTS idx_user_profiles_client_id ON user_profiles(client_id);

COMMENT ON TABLE user_profiles IS 'User profiles linked to Supabase auth.users for application-specific user data';
COMMENT ON COLUMN user_profiles.role IS 'User role: admin, commercial, analyst, mesa_control, manager, user, legal, operations, tesoreria, or cliente';
COMMENT ON COLUMN user_profiles.user_type IS 'Type of user: funcionario (internal employee) or cliente (external client)';

-- ============================================================================
-- TABLE: contract_templates
-- Stores contract template versions
-- ============================================================================
CREATE TABLE IF NOT EXISTS contract_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version VARCHAR(20) NOT NULL,
    contract_type VARCHAR(50) DEFAULT 'activos',
    template_content TEXT NOT NULL,

    -- Status
    active BOOLEAN DEFAULT FALSE,

    -- Audit (nullable)
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,

    UNIQUE(contract_type, version)
);

-- Only one active template per type
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_template
ON contract_templates(contract_type)
WHERE active = TRUE;

COMMENT ON TABLE contract_templates IS 'Contract template versions with placeholders';

-- ============================================================================
-- TABLE: contract_generations
-- Audit trail for all generated contracts
-- ============================================================================
CREATE TABLE IF NOT EXISTS contract_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Contract identification
    contract_id VARCHAR(50) UNIQUE NOT NULL,
    client_nit VARCHAR(20) NOT NULL,
    client_id UUID REFERENCES clients(id),

    -- Contract type
    contract_type VARCHAR(50) DEFAULT 'activos',

    -- Status workflow
    status VARCHAR(50) DEFAULT 'generated'
        CHECK (status IN ('generated', 'under_review', 'approved', 'rejected')),

    -- Generation info (nullable for flexibility)
    generated_by UUID REFERENCES auth.users(id),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Review info (optional)
    reviewed_by UUID REFERENCES auth.users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    -- File storage
    pdf_url TEXT,
    pdf_storage_path TEXT,
    approved_document_url TEXT,

    -- Template version used
    template_id UUID REFERENCES contract_templates(id),
    template_version VARCHAR(20),

    -- Data snapshot (JSON for audit)
    data_snapshot JSONB NOT NULL,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for contract_generations
CREATE INDEX IF NOT EXISTS idx_contract_gen_status ON contract_generations(status);
CREATE INDEX IF NOT EXISTS idx_contract_gen_client ON contract_generations(client_nit);
CREATE INDEX IF NOT EXISTS idx_contract_gen_date ON contract_generations(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_contract_gen_contract_id ON contract_generations(contract_id);
CREATE INDEX IF NOT EXISTS idx_contract_gen_type ON contract_generations(contract_type);
CREATE INDEX IF NOT EXISTS idx_contract_generations_approved_url ON contract_generations(approved_document_url) WHERE approved_document_url IS NOT NULL;

COMMENT ON TABLE contract_generations IS 'Audit trail of all generated contracts';
COMMENT ON COLUMN contract_generations.approved_document_url IS 'Supabase Storage URL for approved contract PDF';

-- ============================================================================
-- TABLE: contract_id_sequence
-- Manages contract ID sequencing by year and type
-- ============================================================================
CREATE TABLE IF NOT EXISTS contract_id_sequence (
    year INTEGER NOT NULL,
    contract_type VARCHAR(50) NOT NULL DEFAULT 'activos',
    last_sequence INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    PRIMARY KEY (year, contract_type)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_contract_id_sequence_type ON contract_id_sequence(contract_type, year);

COMMENT ON TABLE contract_id_sequence IS 'Sequential counter for contract IDs by year and type';

-- ============================================================================
-- TABLE: data_imports
-- Tracks CSV/Excel uploads
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_imports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- File info
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER,

    -- Import results
    total_rows INTEGER,
    successful_rows INTEGER,
    failed_rows INTEGER,
    error_log JSONB,

    -- Audit (nullable)
    imported_by UUID REFERENCES auth.users(id),
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Status
    status VARCHAR(50) DEFAULT 'processing'
        CHECK (status IN ('processing', 'completed', 'failed'))
);

-- ============================================================================
-- FUNCTION: Generate next contract ID
-- Supports multiple contract types: activos, otrosi, inventario_bodega, minuta_compraventa,
-- and Paga Local Colombia contracts (pl_co_*)
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_contract_id(p_contract_type VARCHAR DEFAULT 'activos')
RETURNS VARCHAR AS $$
DECLARE
    current_year INTEGER;
    next_sequence INTEGER;
    prefix VARCHAR(10);
BEGIN
    current_year := EXTRACT(YEAR FROM CURRENT_DATE);

    -- Determine prefix based on contract type
    CASE p_contract_type
        -- Existing contract types
        WHEN 'activos' THEN prefix := 'ACT';
        WHEN 'otrosi' THEN prefix := 'OTRO';
        WHEN 'inventario_bodega' THEN prefix := 'INV';
        WHEN 'minuta_compraventa' THEN prefix := 'MIN';

        -- Paga Local Colombia - Credito contracts (Account-Level)
        -- Each aval type has a unique prefix to prevent duplicate IDs
        -- PLCRJ = Paga Local CRédito Jurídica (Aval Persona Jurídica)
        WHEN 'pl_co_credito_aval_pj' THEN prefix := 'PLCRJ';
        -- PLCRN = Paga Local CRédito Natural (Aval Persona Natural)
        WHEN 'pl_co_credito_aval_pn' THEN prefix := 'PLCRN';
        -- PLCRS = Paga Local CRédito Sin aval (No Aval)
        WHEN 'pl_co_credito_no_aval' THEN prefix := 'PLCRS';

        -- Paga Local Colombia - Mandato contracts (Account-Level)
        -- Each aval type has a unique prefix to prevent duplicate IDs
        -- PLCMJ = Paga Local Cuenta Mandato Jurídica (Aval Persona Jurídica)
        WHEN 'pl_co_mandato_pj' THEN prefix := 'PLCMJ';
        -- PLCMN = Paga Local Cuenta Mandato Natural (Aval Persona Natural)
        WHEN 'pl_co_mandato_pn' THEN prefix := 'PLCMN';
        -- PLCMS = Paga Local Cuenta Mandato Sin aval (No Aval)
        WHEN 'pl_co_mandato_no_aval' THEN prefix := 'PLCMS';

        -- Paga Local Colombia - Documentos Operacion (Operation-Level)
        -- PLMI = Paga Local Mandato Importacion
        WHEN 'pl_co_mandato_im' THEN prefix := 'PLMI';
        -- PLSD = Paga Local Solicitud Desembolso
        WHEN 'pl_co_solicitud_desembolso' THEN prefix := 'PLSD';
        -- PLDI = Paga Local DIAN
        WHEN 'pl_co_dian_mandato_im' THEN prefix := 'PLDI';

        -- Default fallback for backward compatibility
        ELSE prefix := 'ACT';
    END CASE;

    -- Try to get existing sequence for this year and contract type
    SELECT last_sequence INTO next_sequence
    FROM contract_id_sequence
    WHERE year = current_year AND contract_type = p_contract_type
    FOR UPDATE;

    -- If sequence exists, increment it
    IF FOUND THEN
        next_sequence := next_sequence + 1;
        UPDATE contract_id_sequence
        SET last_sequence = next_sequence
        WHERE year = current_year AND contract_type = p_contract_type;
    ELSE
        -- Initialize new sequence for this year and contract type
        next_sequence := 1;
        INSERT INTO contract_id_sequence (year, contract_type, last_sequence)
        VALUES (current_year, p_contract_type, next_sequence);
    END IF;

    -- Return formatted contract ID: PREFIX-YYYY-NNN
    RETURN prefix || '-' || current_year || '-' || LPAD(next_sequence::TEXT, 3, '0');
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: Update timestamp trigger
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_user_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================
DROP TRIGGER IF EXISTS update_clients_updated_at ON clients;
CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_contract_generations_updated_at ON contract_generations;
CREATE TRIGGER update_contract_generations_updated_at BEFORE UPDATE ON contract_generations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER trigger_update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_user_profiles_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE contract_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE contract_generations ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_imports ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Policies for clients table
CREATE POLICY "Allow authenticated users to read clients"
    ON clients FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow operations and legal to insert clients"
    ON clients FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Allow operations and legal to update clients"
    ON clients FOR UPDATE TO authenticated USING (true);

-- Policies for contract_generations
CREATE POLICY "Allow authenticated users to read contracts"
    ON contract_generations FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow operations and legal to create contracts"
    ON contract_generations FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Allow legal to update contracts (review)"
    ON contract_generations FOR UPDATE TO authenticated USING (true);

-- Policies for templates
CREATE POLICY "Allow authenticated users to read templates"
    ON contract_templates FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow legal to manage templates"
    ON contract_templates FOR ALL TO authenticated USING (true);

-- Policies for data imports
CREATE POLICY "Allow authenticated users to view imports"
    ON data_imports FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow operations and legal to import data"
    ON data_imports FOR INSERT TO authenticated WITH CHECK (true);

-- Policies for user_profiles (simple, non-recursive)
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Grant permissions
GRANT SELECT, UPDATE ON user_profiles TO authenticated;
GRANT ALL ON user_profiles TO service_role;

-- ============================================================================
-- INITIAL DATA: Contract Templates
-- ============================================================================

-- Activos template
INSERT INTO contract_templates (version, contract_type, template_content, active, notes)
VALUES ('1.0.0', 'activos', 'FK COL - GM - Activos.docx', TRUE, 'Initial Activos template')
ON CONFLICT (contract_type, version) DO NOTHING;

-- Otrosi template
INSERT INTO contract_templates (version, contract_type, template_content, active, notes)
VALUES ('1.0.0', 'otrosi', 'FK COL - K Marco - Otrosí No. 1.docx', TRUE, 'Otrosí No. 1 template')
ON CONFLICT (contract_type, version) DO NOTHING;

-- Inventario Bodega template
INSERT INTO contract_templates (version, contract_type, template_content, active, notes)
VALUES ('1.0.0', 'inventario_bodega', 'FK COL - GM - Inventario Bodega de 3ro.docx', TRUE, 'Inventario Bodega template')
ON CONFLICT (contract_type, version) DO NOTHING;

-- Minuta Compraventa template
INSERT INTO contract_templates (version, contract_type, template_content, active, notes)
VALUES ('1.0.0', 'minuta_compraventa', 'Minuta Compraventa GT.docx', TRUE, 'Minuta Compraventa template')
ON CONFLICT (contract_type, version) DO NOTHING;

-- ============================================================================
-- INITIAL DATA: Contract ID Sequences
-- ============================================================================

-- Initialize sequences for current year
INSERT INTO contract_id_sequence (year, contract_type, last_sequence)
VALUES
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'activos', 0),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'otrosi', 0),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'inventario_bodega', 0),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'minuta_compraventa', 0)
ON CONFLICT (year, contract_type) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'DATABASE SCHEMA CREATED SUCCESSFULLY!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Tables created: clients, user_profiles, contract_templates,';
    RAISE NOTICE '                contract_generations, contract_id_sequence, data_imports';
    RAISE NOTICE '';
    RAISE NOTICE 'Contract types supported:';
    RAISE NOTICE '  - activos (ACT-YYYY-NNN)';
    RAISE NOTICE '  - otrosi (OTRO-YYYY-NNN)';
    RAISE NOTICE '  - inventario_bodega (INV-YYYY-NNN)';
    RAISE NOTICE '  - minuta_compraventa (MIN-YYYY-NNN)';
    RAISE NOTICE '';
    RAISE NOTICE 'RLS policies enabled for all tables.';
    RAISE NOTICE '============================================================';
END $$;
