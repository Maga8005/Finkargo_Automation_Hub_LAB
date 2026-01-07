-- Migration: Create Alianzas (Partnerships) Module Tables
-- Date: 2025-12-10
-- Description: Creates tables for broker management, commissions, and payments
-- Prerequisites: migration_add_alianzas_role.sql must be applied first

-- ============================================================================
-- TABLE: brokers
-- ============================================================================
-- Stores broker/partner information with support for master broker hierarchies

CREATE TABLE IF NOT EXISTS brokers (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Broker identification
    nombre VARCHAR(255) NOT NULL,
    tipo_broker VARCHAR(50) NOT NULL CHECK (tipo_broker IN ('master_broker', 'independiente', 'aliado_logistico', 'consultoria')),

    -- Hierarchy (self-referencing for master broker relationships)
    master_broker_id UUID REFERENCES brokers(id) ON DELETE SET NULL,

    -- Commission rates
    porcentaje_apertura DECIMAL(5,2),  -- e.g., 60.00 for 60%
    porcentaje_operativa DECIMAL(5,3), -- e.g., 0.100 for 0.10%

    -- Banking information
    cuenta_bancaria VARCHAR(50),
    banco VARCHAR(100),

    -- Tax identification (Mexico)
    rfc VARCHAR(20),

    -- Contract dates
    fecha_contrato DATE,
    vigencia_contrato DATE,

    -- Status
    estado VARCHAR(20) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'pendiente')),

    -- Documentation
    link_expediente TEXT,
    notas TEXT,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- ============================================================================
-- TABLE: broker_comisiones
-- ============================================================================
-- Tracks commission calculations per broker, period, and client

CREATE TABLE IF NOT EXISTS broker_comisiones (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Broker reference
    broker_id UUID NOT NULL REFERENCES brokers(id) ON DELETE CASCADE,

    -- Period
    periodo_mes INTEGER NOT NULL CHECK (periodo_mes BETWEEN 1 AND 12),
    periodo_anio INTEGER NOT NULL CHECK (periodo_anio >= 2020),

    -- Client information
    cliente_nombre VARCHAR(255),
    cliente_nit VARCHAR(50),

    -- Commission type
    tipo_comision VARCHAR(20) NOT NULL CHECK (tipo_comision IN ('apertura', 'operativa')),

    -- Commission calculation fields
    linea_credito DECIMAL(15,2),
    porcentaje_comision_cliente DECIMAL(5,2),
    monto_comision_cliente DECIMAL(15,2),
    porcentaje_broker DECIMAL(5,3),
    monto_broker_usd DECIMAL(15,2),

    -- Operations and currency
    operaciones_mes DECIMAL(15,2),
    tipo_cambio DECIMAL(10,4),
    monto_broker_mxn DECIMAL(15,2),
    cliente_pago_pct DECIMAL(5,2),

    -- Status
    estado VARCHAR(20) NOT NULL DEFAULT 'calculado' CHECK (estado IN ('calculado', 'aprobado', 'pagado')),

    -- Notes
    notas TEXT,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- ============================================================================
-- TABLE: broker_pagos
-- ============================================================================
-- Tracks payment records for brokers

CREATE TABLE IF NOT EXISTS broker_pagos (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Broker reference
    broker_id UUID NOT NULL REFERENCES brokers(id) ON DELETE CASCADE,

    -- Period
    periodo_mes INTEGER NOT NULL CHECK (periodo_mes BETWEEN 1 AND 12),
    periodo_anio INTEGER NOT NULL CHECK (periodo_anio >= 2020),

    -- Payment amounts
    total_usd DECIMAL(15,2) NOT NULL,
    total_mxn DECIMAL(15,2) NOT NULL,
    tipo_cambio DECIMAL(10,4) NOT NULL,

    -- Payment dates
    fecha_programada DATE,
    fecha_pago DATE,

    -- Status
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'programado', 'pagado')),

    -- Documentation URLs
    comprobante_url TEXT,
    factura_broker_url TEXT,

    -- Notes
    notas TEXT,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_by UUID REFERENCES auth.users(id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for filtering brokers by estado
CREATE INDEX IF NOT EXISTS idx_brokers_estado ON brokers(estado);

-- Composite index for commission period queries
CREATE INDEX IF NOT EXISTS idx_broker_comisiones_periodo ON broker_comisiones(periodo_anio, periodo_mes);

-- Index for commission lookups by broker
CREATE INDEX IF NOT EXISTS idx_broker_comisiones_broker ON broker_comisiones(broker_id);

-- Index for payment lookups by broker
CREATE INDEX IF NOT EXISTS idx_broker_pagos_broker ON broker_pagos(broker_id);

-- Index for filtering payments by estado
CREATE INDEX IF NOT EXISTS idx_broker_pagos_estado ON broker_pagos(estado);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to auto-update updated_at on brokers table
CREATE OR REPLACE FUNCTION update_brokers_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_brokers_updated_at ON brokers;
CREATE TRIGGER trigger_brokers_updated_at
    BEFORE UPDATE ON brokers
    FOR EACH ROW
    EXECUTE FUNCTION update_brokers_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE brokers ENABLE ROW LEVEL SECURITY;
ALTER TABLE broker_comisiones ENABLE ROW LEVEL SECURITY;
ALTER TABLE broker_pagos ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- BROKERS TABLE POLICIES
-- -----------------------------------------------------------------------------

-- SELECT: All authenticated users can read
CREATE POLICY "Authenticated users can read brokers"
ON brokers FOR SELECT
TO authenticated
USING (true);

-- INSERT: Only admin or alianzas role
CREATE POLICY "Admin and alianzas can insert brokers"
ON brokers FOR INSERT
TO authenticated
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role IN ('admin', 'alianzas')
        AND user_profiles.is_active = true
    )
);

-- UPDATE: Only admin or alianzas role
CREATE POLICY "Admin and alianzas can update brokers"
ON brokers FOR UPDATE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role IN ('admin', 'alianzas')
        AND user_profiles.is_active = true
    )
);

-- DELETE: Only admin or alianzas role
CREATE POLICY "Admin and alianzas can delete brokers"
ON brokers FOR DELETE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role IN ('admin', 'alianzas')
        AND user_profiles.is_active = true
    )
);

-- Service role has full access
CREATE POLICY "Service role has full access to brokers"
ON brokers FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- -----------------------------------------------------------------------------
-- BROKER_COMISIONES TABLE POLICIES
-- -----------------------------------------------------------------------------

-- SELECT: All authenticated users can read
CREATE POLICY "Authenticated users can read broker_comisiones"
ON broker_comisiones FOR SELECT
TO authenticated
USING (true);

-- INSERT: Only admin or alianzas role
CREATE POLICY "Admin and alianzas can insert broker_comisiones"
ON broker_comisiones FOR INSERT
TO authenticated
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role IN ('admin', 'alianzas')
        AND user_profiles.is_active = true
    )
);

-- UPDATE: Only admin or alianzas role
CREATE POLICY "Admin and alianzas can update broker_comisiones"
ON broker_comisiones FOR UPDATE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role IN ('admin', 'alianzas')
        AND user_profiles.is_active = true
    )
);

-- DELETE: Only admin or alianzas role
CREATE POLICY "Admin and alianzas can delete broker_comisiones"
ON broker_comisiones FOR DELETE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role IN ('admin', 'alianzas')
        AND user_profiles.is_active = true
    )
);

-- Service role has full access
CREATE POLICY "Service role has full access to broker_comisiones"
ON broker_comisiones FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- -----------------------------------------------------------------------------
-- BROKER_PAGOS TABLE POLICIES
-- -----------------------------------------------------------------------------

-- SELECT: All authenticated users can read
CREATE POLICY "Authenticated users can read broker_pagos"
ON broker_pagos FOR SELECT
TO authenticated
USING (true);

-- INSERT: Only admin or alianzas role
CREATE POLICY "Admin and alianzas can insert broker_pagos"
ON broker_pagos FOR INSERT
TO authenticated
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role IN ('admin', 'alianzas')
        AND user_profiles.is_active = true
    )
);

-- UPDATE: Only admin or alianzas role
CREATE POLICY "Admin and alianzas can update broker_pagos"
ON broker_pagos FOR UPDATE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role IN ('admin', 'alianzas')
        AND user_profiles.is_active = true
    )
);

-- DELETE: Only admin or alianzas role
CREATE POLICY "Admin and alianzas can delete broker_pagos"
ON broker_pagos FOR DELETE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role IN ('admin', 'alianzas')
        AND user_profiles.is_active = true
    )
);

-- Service role has full access
CREATE POLICY "Service role has full access to broker_pagos"
ON broker_pagos FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE brokers IS 'Stores broker/partner information for the Alianzas department with support for master broker hierarchies';
COMMENT ON COLUMN brokers.tipo_broker IS 'Type of broker: master_broker, independiente, aliado_logistico, consultoria';
COMMENT ON COLUMN brokers.master_broker_id IS 'Self-referencing FK for sub-broker relationships under a master broker';
COMMENT ON COLUMN brokers.porcentaje_apertura IS 'Opening commission percentage, e.g., 60.00 for 60%';
COMMENT ON COLUMN brokers.porcentaje_operativa IS 'Operational commission percentage, e.g., 0.100 for 0.10%';
COMMENT ON COLUMN brokers.rfc IS 'Mexican tax identification number (RFC)';
COMMENT ON COLUMN brokers.estado IS 'Broker status: activo, inactivo, pendiente';

COMMENT ON TABLE broker_comisiones IS 'Tracks commission calculations per broker, period, and client';
COMMENT ON COLUMN broker_comisiones.tipo_comision IS 'Commission type: apertura (opening) or operativa (operational)';
COMMENT ON COLUMN broker_comisiones.monto_broker_usd IS 'Broker commission amount in USD';
COMMENT ON COLUMN broker_comisiones.monto_broker_mxn IS 'Broker commission amount in MXN';
COMMENT ON COLUMN broker_comisiones.estado IS 'Commission status: calculado, aprobado, pagado';

COMMENT ON TABLE broker_pagos IS 'Tracks payment records for brokers';
COMMENT ON COLUMN broker_pagos.estado IS 'Payment status: pendiente, programado, pagado';
COMMENT ON COLUMN broker_pagos.comprobante_url IS 'URL to payment receipt document';
COMMENT ON COLUMN broker_pagos.factura_broker_url IS 'URL to broker invoice document';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify tables were created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('brokers', 'broker_comisiones', 'broker_pagos');

-- Verify indexes
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public'
AND indexname LIKE 'idx_broker%';

-- Verify RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('brokers', 'broker_comisiones', 'broker_pagos');
