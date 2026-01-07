# Database Setup - Legal Contract Automation

## Quick Start

### 1. Run Schema in Supabase

1. Go to your Supabase project: https://swkkbpmvsabarntswumm.supabase.co
2. Navigate to **SQL Editor**
3. Create a new query
4. Copy and paste the entire contents of `schema.sql`
5. Click **Run** to execute

### 2. Verify Tables Created

Run this query to verify all tables were created:

```sql
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('clients', 'contract_templates', 'contract_generations', 'contract_id_sequence', 'data_imports');
```

You should see all 5 tables listed.

### 3. Test Contract ID Generation

Test the contract ID generation function:

```sql
SELECT generate_contract_id();
```

Should return something like: `ACT-2025-001`

### 4. View Sample Data

```sql
-- View sample clients
SELECT * FROM clients;

-- View active template
SELECT version, contract_type, active
FROM contract_templates
WHERE active = TRUE;
```

## Tables Overview

| Table | Purpose |
|-------|---------|
| `clients` | Client data imported from Excel/CSV |
| `contract_templates` | Contract template versions |
| `contract_generations` | Audit trail of generated contracts |
| `contract_id_sequence` | Sequential counter for contract IDs by year |
| `data_imports` | History of CSV/Excel imports |

## Important Notes

- **Row Level Security (RLS)** is enabled on all tables
- **Sample data** includes 2 test clients and 1 template version
- **Contract IDs** are generated automatically using format: `ACT-YYYY-NNN`
- **Timestamps** are automatically managed with triggers

## Next Steps

After running the schema:

1. Update backend connection string in `.env`
2. Test API endpoints with sample data
3. Import real client data via CSV upload feature
4. Upload actual contract template from Sofia

## Troubleshooting

**Issue**: Permission denied when creating tables
**Solution**: Ensure you're logged in as the project owner or have sufficient permissions

**Issue**: Constraint violation errors
**Solution**: Drop existing tables first:
```sql
DROP TABLE IF EXISTS data_imports CASCADE;
DROP TABLE IF EXISTS contract_generations CASCADE;
DROP TABLE IF EXISTS contract_id_sequence CASCADE;
DROP TABLE IF EXISTS contract_templates CASCADE;
DROP TABLE IF EXISTS clients CASCADE;
```

Then re-run the schema.sql file.
