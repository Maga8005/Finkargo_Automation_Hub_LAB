-- Migration: Add finance_reports table for tracking invoice report generation history
-- Date: 2024-11-28
-- Description: Creates a table to track all finance report generations for CO and MX

-- ============================================================================
-- TABLE: finance_reports
-- ============================================================================
-- Tracks all invoice report generations from the Finance/Billing team
-- Supports both Colombia (CO) and Mexico (MX) operations

CREATE TABLE IF NOT EXISTS finance_reports (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Report identification
    report_id VARCHAR(50) UNIQUE NOT NULL,  -- Format: FIN-CO-2025-0001 or FIN-MX-2025-0001
    country VARCHAR(2) NOT NULL CHECK (country IN ('CO', 'MX')),

    -- Report type
    report_type VARCHAR(50) NOT NULL DEFAULT 'facturacion',  -- facturacion, consulta, zip_download

    -- Status workflow
    status VARCHAR(50) NOT NULL DEFAULT 'completed' CHECK (status IN ('processing', 'completed', 'failed', 'downloaded')),

    -- Generation info
    generated_by UUID REFERENCES auth.users(id),
    generated_by_email VARCHAR(255),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Report statistics (JSONB for flexibility)
    stats JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Example CO stats: {"total_records_noova": 100, "total_records_netsuite": 95, "costos_fijos_count": 80, "mandato_count": 20}
    -- Example MX stats: {"total_invoices": 50, "matched_pdfs": 45}

    -- Filter criteria used (for consulta/filter reports)
    filters_applied JSONB DEFAULT NULL,
    -- Example: {"nit": "900123456", "operaciones": ["OP001", "OP002"], "fecha_inicio": "2025-01-01"}

    -- File information
    file_name VARCHAR(255),
    file_size_bytes BIGINT,
    drive_uploaded BOOLEAN DEFAULT FALSE,
    drive_url TEXT,

    -- Session tracking (for download capability)
    session_id VARCHAR(100),

    -- Error tracking
    error_message TEXT,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES for fast queries
-- ============================================================================

-- Index for filtering by country
CREATE INDEX idx_finance_reports_country ON finance_reports(country);

-- Index for filtering by status
CREATE INDEX idx_finance_reports_status ON finance_reports(status);

-- Index for date range queries (most recent first)
CREATE INDEX idx_finance_reports_date ON finance_reports(generated_at DESC);

-- Index for user queries
CREATE INDEX idx_finance_reports_user ON finance_reports(generated_by);

-- Index for report type
CREATE INDEX idx_finance_reports_type ON finance_reports(report_type);

-- Composite index for common filter combination
CREATE INDEX idx_finance_reports_country_date ON finance_reports(country, generated_at DESC);

-- ============================================================================
-- SEQUENCE for report_id generation
-- ============================================================================

-- Sequence for CO reports
CREATE SEQUENCE IF NOT EXISTS finance_report_co_seq START 1;

-- Sequence for MX reports
CREATE SEQUENCE IF NOT EXISTS finance_report_mx_seq START 1;

-- ============================================================================
-- FUNCTION to generate report_id
-- ============================================================================

CREATE OR REPLACE FUNCTION generate_finance_report_id(p_country VARCHAR(2))
RETURNS VARCHAR(50) AS $$
DECLARE
    v_year VARCHAR(4);
    v_seq INTEGER;
    v_report_id VARCHAR(50);
BEGIN
    v_year := TO_CHAR(NOW(), 'YYYY');

    IF p_country = 'CO' THEN
        v_seq := NEXTVAL('finance_report_co_seq');
    ELSIF p_country = 'MX' THEN
        v_seq := NEXTVAL('finance_report_mx_seq');
    ELSE
        RAISE EXCEPTION 'Invalid country code: %', p_country;
    END IF;

    v_report_id := 'FIN-' || p_country || '-' || v_year || '-' || LPAD(v_seq::TEXT, 4, '0');

    RETURN v_report_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER to auto-update updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_finance_reports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_finance_reports_updated_at
    BEFORE UPDATE ON finance_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_finance_reports_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE finance_reports ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read all reports
CREATE POLICY "Authenticated users can read finance reports"
ON finance_reports FOR SELECT
TO authenticated
USING (true);

-- Policy: Authenticated users can insert reports
CREATE POLICY "Authenticated users can create finance reports"
ON finance_reports FOR INSERT
TO authenticated
WITH CHECK (true);

-- Policy: Users can update their own reports
CREATE POLICY "Users can update own finance reports"
ON finance_reports FOR UPDATE
TO authenticated
USING (generated_by = auth.uid());

-- Policy: Service role has full access
CREATE POLICY "Service role has full access to finance reports"
ON finance_reports FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE finance_reports IS 'Tracks all finance/billing report generations for CO and MX operations';
COMMENT ON COLUMN finance_reports.report_id IS 'Business identifier format: FIN-{CO|MX}-YYYY-NNNN';
COMMENT ON COLUMN finance_reports.country IS 'Country code: CO (Colombia) or MX (Mexico)';
COMMENT ON COLUMN finance_reports.report_type IS 'Type of report: facturacion (upload+process), consulta (filter), zip_download (with PDFs)';
COMMENT ON COLUMN finance_reports.stats IS 'JSON object with report statistics (records processed, matched, etc.)';
COMMENT ON COLUMN finance_reports.filters_applied IS 'JSON object with filter criteria used for consulta reports';
