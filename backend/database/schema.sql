-- Finkargo Automation Hub - Legal Contract Automation Schema
-- Database: Supabase PostgreSQL
-- Created: 2025-10-04

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- TABLE: clients
-- Stores client data imported from Excel/CSV
-- Source: Daily uploads from Superset export
-- =============================================
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nit VARCHAR(20) UNIQUE NOT NULL,
    nombre_importador VARCHAR(255) NOT NULL,
    representante_legal VARCHAR(255) NOT NULL,
    cedula_representante VARCHAR(50) NOT NULL,
    ciudad_domicilio VARCHAR(100) NOT NULL,
    cupo_plataforma DECIMAL(15, 2) NOT NULL,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    imported_by UUID REFERENCES auth.users(id),

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT
);

-- Index for fast search
CREATE INDEX idx_clients_nit ON clients(nit);
CREATE INDEX idx_clients_nombre ON clients(nombre_importador);
CREATE INDEX idx_clients_active ON clients(is_active);

-- =============================================
-- TABLE: contract_templates
-- Stores contract template versions
-- =============================================
CREATE TABLE IF NOT EXISTS contract_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version VARCHAR(20) NOT NULL,
    contract_type VARCHAR(50) DEFAULT 'activos',
    template_content TEXT NOT NULL,

    -- Status
    active BOOLEAN DEFAULT FALSE,

    -- Audit
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,

    UNIQUE(contract_type, version)
);

-- Only one active template per type
CREATE UNIQUE INDEX idx_one_active_template
ON contract_templates(contract_type)
WHERE active = TRUE;

-- =============================================
-- TABLE: contract_generations
-- Audit trail for all generated contracts
-- =============================================
CREATE TABLE IF NOT EXISTS contract_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Contract identification
    contract_id VARCHAR(50) UNIQUE NOT NULL, -- ACT-2025-001
    client_nit VARCHAR(20) NOT NULL,
    client_id UUID REFERENCES clients(id),

    -- Status workflow
    status VARCHAR(50) DEFAULT 'generated'
        CHECK (status IN ('generated', 'under_review', 'approved', 'rejected')),

    -- Generation info
    generated_by UUID REFERENCES auth.users(id) NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Review info (optional)
    reviewed_by UUID REFERENCES auth.users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    -- File storage
    pdf_url TEXT,
    pdf_storage_path TEXT,

    -- Template version used
    template_id UUID REFERENCES contract_templates(id),
    template_version VARCHAR(20),

    -- Data snapshot (JSON for audit)
    data_snapshot JSONB NOT NULL,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_contract_gen_status ON contract_generations(status);
CREATE INDEX idx_contract_gen_client ON contract_generations(client_nit);
CREATE INDEX idx_contract_gen_date ON contract_generations(generated_at DESC);
CREATE INDEX idx_contract_gen_contract_id ON contract_generations(contract_id);

-- =============================================
-- TABLE: contract_id_sequence
-- Manages contract ID sequencing by year
-- =============================================
CREATE TABLE IF NOT EXISTS contract_id_sequence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    year INTEGER NOT NULL,
    last_sequence INTEGER DEFAULT 0,

    UNIQUE(year)
);

-- =============================================
-- TABLE: data_imports
-- Tracks CSV/Excel uploads
-- =============================================
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

    -- Audit
    imported_by UUID REFERENCES auth.users(id),
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Status
    status VARCHAR(50) DEFAULT 'processing'
        CHECK (status IN ('processing', 'completed', 'failed'))
);

-- =============================================
-- FUNCTION: Generate next contract ID
-- =============================================
CREATE OR REPLACE FUNCTION generate_contract_id()
RETURNS VARCHAR AS $$
DECLARE
    current_year INTEGER;
    next_sequence INTEGER;
    new_contract_id VARCHAR(50);
BEGIN
    current_year := EXTRACT(YEAR FROM CURRENT_DATE);

    -- Insert or update sequence for current year
    INSERT INTO contract_id_sequence (year, last_sequence)
    VALUES (current_year, 1)
    ON CONFLICT (year)
    DO UPDATE SET last_sequence = contract_id_sequence.last_sequence + 1
    RETURNING last_sequence INTO next_sequence;

    -- Format: ACT-YYYY-NNN
    new_contract_id := 'ACT-' || current_year || '-' || LPAD(next_sequence::TEXT, 3, '0');

    RETURN new_contract_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- FUNCTION: Update timestamp trigger
-- =============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contract_generations_updated_at BEFORE UPDATE ON contract_generations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================

-- Enable RLS
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE contract_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE contract_generations ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_imports ENABLE ROW LEVEL SECURITY;

-- Policies for clients table
CREATE POLICY "Allow authenticated users to read clients"
    ON clients FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow operations and legal to insert clients"
    ON clients FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Allow operations and legal to update clients"
    ON clients FOR UPDATE
    TO authenticated
    USING (true);

-- Policies for contract_generations
CREATE POLICY "Allow authenticated users to read contracts"
    ON contract_generations FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow operations and legal to create contracts"
    ON contract_generations FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Allow legal to update contracts (review)"
    ON contract_generations FOR UPDATE
    TO authenticated
    USING (true);

-- Policies for templates
CREATE POLICY "Allow authenticated users to read templates"
    ON contract_templates FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow legal to manage templates"
    ON contract_templates FOR ALL
    TO authenticated
    USING (true);

-- Policies for data imports
CREATE POLICY "Allow authenticated users to view imports"
    ON data_imports FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow operations and legal to import data"
    ON data_imports FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- =============================================
-- SAMPLE DATA (for testing)
-- =============================================

-- Insert initial template version
INSERT INTO contract_templates (version, contract_type, template_content, active, notes)
VALUES
    ('1.0.0', 'activos', 'Template content will be added from Word doc', TRUE, 'Initial template version')
ON CONFLICT DO NOTHING;

-- Insert sample client data
INSERT INTO clients (nit, nombre_importador, representante_legal, cedula_representante, ciudad_domicilio, cupo_plataforma)
VALUES
    ('900123456-1', 'Importadora XYZ S.A.S.', 'Juan Pérez', '1234567890', 'Bogotá', 300000000.00),
    ('900987654-2', 'Comercial ABC Ltda', 'María García', '0987654321', 'Medellín', 150000000.00)
ON CONFLICT DO NOTHING;

COMMENT ON TABLE clients IS 'Client data imported from platform exports';
COMMENT ON TABLE contract_templates IS 'Contract template versions with placeholders';
COMMENT ON TABLE contract_generations IS 'Audit trail of all generated contracts';
COMMENT ON TABLE contract_id_sequence IS 'Sequential counter for contract IDs by year';
COMMENT ON TABLE data_imports IS 'History of CSV/Excel data imports';
