-- Migration: Create Risk Management Tables
-- Date: 2025-12-21
-- Description: Creates tables for fraud detection and risk assessment system
--              Including risk_assessments, fraud_detection_rules, risk_blacklist, and risk_alerts

-- ==================== SEQUENCE FOR RISK ASSESSMENT IDS ====================

-- Create sequence for risk assessment IDs
CREATE SEQUENCE IF NOT EXISTS risk_assessment_id_seq START WITH 1;

-- Function to generate risk assessment business ID (RISK-YYYY-NNN)
CREATE OR REPLACE FUNCTION generate_risk_assessment_id()
RETURNS VARCHAR(20) AS $$
DECLARE
    current_year INTEGER;
    seq_value INTEGER;
    assessment_id VARCHAR(20);
BEGIN
    current_year := EXTRACT(YEAR FROM CURRENT_DATE);

    -- Get next sequence value
    seq_value := nextval('risk_assessment_id_seq');

    -- Format: RISK-YYYY-NNN (e.g., RISK-2025-001)
    assessment_id := 'RISK-' || current_year || '-' || LPAD(seq_value::TEXT, 3, '0');

    RETURN assessment_id;
END;
$$ LANGUAGE plpgsql;

-- ==================== RISK ASSESSMENTS TABLE ====================

CREATE TABLE IF NOT EXISTS risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id VARCHAR(20) UNIQUE NOT NULL DEFAULT generate_risk_assessment_id(),
    client_nit VARCHAR(50) NOT NULL,
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    risk_score DECIMAL(5,2) NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
    fraud_indicators JSONB NOT NULL DEFAULT '[]',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'escalated', 'approved', 'rejected')),
    assessment_type VARCHAR(50) NOT NULL DEFAULT 'comprehensive',
    assessed_by UUID REFERENCES user_profiles(id),
    assessed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,
    client_data_snapshot JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for risk_assessments
CREATE INDEX IF NOT EXISTS idx_risk_assessments_client_nit ON risk_assessments(client_nit);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_status ON risk_assessments(status);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_risk_level ON risk_assessments(risk_level);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_created_at ON risk_assessments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_assessed_by ON risk_assessments(assessed_by);

-- ==================== FRAUD DETECTION RULES TABLE ====================

CREATE TABLE IF NOT EXISTS fraud_detection_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(100) UNIQUE NOT NULL,
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('identity', 'email', 'document', 'nit', 'address', 'financial', 'history')),
    description TEXT,
    weight DECIMAL(3,2) NOT NULL DEFAULT 0.10 CHECK (weight >= 0 AND weight <= 1),
    threshold DECIMAL(5,2) DEFAULT 50.00,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fraud_detection_rules
CREATE INDEX IF NOT EXISTS idx_fraud_rules_active ON fraud_detection_rules(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_fraud_rules_type ON fraud_detection_rules(rule_type);

-- Insert default fraud detection rules
INSERT INTO fraud_detection_rules (rule_name, rule_type, description, weight, threshold, is_active, config) VALUES
    ('identity_consistency', 'identity', 'Verifica consistencia del nombre de empresa en todos los documentos', 0.35, 50.00, TRUE, '{"check_company_name": true, "check_representative": true}'),
    ('email_domain_validation', 'email', 'Detecta dominios de email sospechosos o similares a empresas conocidas (typosquatting)', 0.25, 70.00, TRUE, '{"check_typosquatting": true, "suspicious_tlds": [".xyz", ".top", ".tk"]}'),
    ('nit_format_validation', 'nit', 'Valida formato y dígito de verificación del NIT colombiano', 0.10, 80.00, TRUE, '{"country": "CO", "format": "XXX.XXX.XXX-X"}'),
    ('document_metadata', 'document', 'Analiza metadatos de documentos para detectar manipulación', 0.10, 60.00, TRUE, '{"check_creation_date": true, "check_author": true}'),
    ('company_history', 'history', 'Verifica antigüedad y historial de la empresa', 0.10, 50.00, TRUE, '{"min_years": 2, "check_legal_status": true}'),
    ('address_verification', 'address', 'Verifica consistencia de direcciones comerciales', 0.10, 50.00, TRUE, '{"check_consistency": true, "validate_city": true}')
ON CONFLICT (rule_name) DO NOTHING;

-- ==================== RISK BLACKLIST TABLE ====================

CREATE TABLE IF NOT EXISTS risk_blacklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('nit', 'email_domain', 'company_name', 'person_id', 'address', 'phone')),
    entity_value VARCHAR(500) NOT NULL,
    reason TEXT NOT NULL,
    source VARCHAR(100) DEFAULT 'manual',
    added_by UUID REFERENCES user_profiles(id),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(entity_type, entity_value)
);

-- Indexes for risk_blacklist
CREATE INDEX IF NOT EXISTS idx_blacklist_entity_type ON risk_blacklist(entity_type);
CREATE INDEX IF NOT EXISTS idx_blacklist_entity_value ON risk_blacklist(entity_value);
CREATE INDEX IF NOT EXISTS idx_blacklist_active ON risk_blacklist(is_active) WHERE is_active = TRUE;

-- ==================== RISK ALERTS TABLE ====================

CREATE TABLE IF NOT EXISTS risk_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES risk_assessments(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('new_critical', 'escalation', 'threshold_breach', 'blacklist_match', 'review_required')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_by UUID REFERENCES user_profiles(id),
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for risk_alerts
CREATE INDEX IF NOT EXISTS idx_risk_alerts_assessment ON risk_alerts(assessment_id);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_unread ON risk_alerts(is_read) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_risk_alerts_severity ON risk_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_created_at ON risk_alerts(created_at DESC);

-- ==================== ROW LEVEL SECURITY ====================

-- Enable RLS on all risk tables
ALTER TABLE risk_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_detection_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_blacklist ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_alerts ENABLE ROW LEVEL SECURITY;

-- RLS Policies for risk_assessments
CREATE POLICY "Authenticated users can view risk assessments"
ON risk_assessments FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Risk roles can insert risk assessments"
ON risk_assessments FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Risk roles can update risk assessments"
ON risk_assessments FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

-- RLS Policies for fraud_detection_rules
CREATE POLICY "Authenticated users can view fraud rules"
ON fraud_detection_rules FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Risk managers can update fraud rules"
ON fraud_detection_rules FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

-- RLS Policies for risk_blacklist
CREATE POLICY "Authenticated users can view blacklist"
ON risk_blacklist FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Risk roles can manage blacklist"
ON risk_blacklist FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Risk roles can update blacklist"
ON risk_blacklist FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Risk managers can delete from blacklist"
ON risk_blacklist FOR DELETE
TO authenticated
USING (true);

-- RLS Policies for risk_alerts
CREATE POLICY "Authenticated users can view alerts"
ON risk_alerts FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "System can create alerts"
ON risk_alerts FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Users can update alerts they read"
ON risk_alerts FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

-- ==================== TRIGGER FOR UPDATED_AT ====================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for risk_assessments
DROP TRIGGER IF EXISTS update_risk_assessments_updated_at ON risk_assessments;
CREATE TRIGGER update_risk_assessments_updated_at
    BEFORE UPDATE ON risk_assessments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for fraud_detection_rules
DROP TRIGGER IF EXISTS update_fraud_rules_updated_at ON fraud_detection_rules;
CREATE TRIGGER update_fraud_rules_updated_at
    BEFORE UPDATE ON fraud_detection_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==================== VERIFICATION ====================

-- Verify tables were created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('risk_assessments', 'fraud_detection_rules', 'risk_blacklist', 'risk_alerts')
ORDER BY table_name;

-- Verify default rules were inserted
SELECT rule_name, rule_type, weight, is_active
FROM fraud_detection_rules
ORDER BY weight DESC;
