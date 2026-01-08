# Requirements Analysis: Legal Contract Automation - Asset Guarantee Contracts

## Executive Summary

**Problem Statement:** The Legal team manually creates 3-15 asset guarantee contracts per day using Word templates, creating bottlenecks for Operations and Commercial teams. All required data already exists in the platform, making this an ideal automation candidate.

**Impact:** 
- Legal team congestion (daily workload)
- Operational delays in payment processing
- Slower client experience
- Inefficient use of legal resources on templated documents

---

## Business Context

### Current State
- **Merchandise Guarantee Contracts**: Already automated in official platform (mandatory for all clients)
- **Asset Guarantee Contracts**: Manual process via Legal team (3-15 per day)
- **Third Contract Type**: Mentioned but not yet detailed

### Trigger Event
Asset guarantee contracts are required when the merchandise guarantee doesn't provide sufficient coverage for the loan amount.

**Example:** 
- Loan amount: $300,000
- Merchandise guarantee coverage: $100,000
- Asset guarantee needed: $200,000+ to reach full coverage

---

## Current Workflow (Manual Process)

### Process Steps
1. **Operations** reviews guarantee coverage in their Excel tracker
2. **Operations** identifies insufficient coverage (merchandise guarantee < loan amount)
3. **Operations** requests asset guarantee contract from Legal via email
4. **Legal (Sofia)** receives request
5. **Legal** opens Word template with blank fields
6. **Legal** logs into platform to retrieve client data
7. **Legal** manually copies data from platform to Word template:
   - Importer name
   - Tax ID (NIT)
   - Legal representative name
   - Legal representative ID number
   - City of domicile
   - Credit limit from platform
8. **Legal** saves as PDF
9. **Legal** sends PDF via email to Operations
10. **Operations** uploads to platform
11. **Operations** uploads to DocuSign for signature
12. **Client** signs via DocuSign
13. **Operations** uploads signed contract to platform
14. **Operations** releases payment

### Pain Points
- **Time per contract**: 15 minutes creation + handling
- **Daily volume**: 3-4 contracts minimum, up to 15 on busy days
- **Bottleneck**: Legal team is the blocker for payment release
- **Manual data entry**: All data already exists in platform
- **Context switching**: Legal must stop other work to create contracts
- **No SLA**: Commercial teams push urgency, but Legal is overwhelmed

---

## Functional Requirements

### FR-1: Contract Generation Interface
**Priority:** High

**Description:** Create a module in the Finkargo Automation Hub where Operations can generate asset guarantee contracts without Legal intervention.

**User Story:** As an Operations team member, I want to generate asset guarantee contracts directly so that I don't have to wait for Legal and can process payments faster.

**Acceptance Criteria:**
- [ ] User can access application with proper authentication
- [ ] User can search/select client by name or tax ID (NIT)
- [ ] System retrieves all required data from Finkargo platform
- [ ] System auto-fills contract template with platform data
- [ ] User can preview generated contract before finalizing
- [ ] System generates PDF output
- [ ] User can download generated PDF
- [ ] System logs all contract generations with timestamp and user

---

### FR-2: Platform Data Integration
**Priority:** High

**Description:** Automatically retrieve client data from Finkargo platform database.

**Data Fields Required:**
| Field | Source | Notes |
|-------|--------|-------|
| Importer name | Platform | Company legal name |
| Tax ID (NIT) | Platform | Colombian tax identifier |
| Legal representative name | Platform | Signatory for contract |
| Legal representative ID | Platform | Cédula number |
| City of domicile | Platform | Legal address city |
| Credit limit | Platform | Approved credit line |

**Acceptance Criteria:**
- [ ] API endpoint to retrieve client data by NIT or name
- [ ] Data validation to ensure all required fields are present
- [ ] Error handling for missing or incomplete data
- [ ] Response time < 2 seconds for data retrieval

---

### FR-3: Document Template Management
**Priority:** High

**Description:** Store and manage contract template with dynamic field replacement.

**User Story:** As a Legal team member, I want to update contract templates when legal requirements change, without requiring developer intervention.

**Acceptance Criteria:**
- [ ] Template stored with clearly marked placeholders for dynamic data
- [ ] Support for 20-page contract format (current contract length)
- [ ] Maintain proper legal formatting and structure
- [ ] Template version control (track changes)
- [ ] Admin interface to upload new template versions
- [ ] Validation that all required placeholders exist in template

**Template Placeholders:**
```
{{IMPORTER_NAME}}
{{TAX_ID}}
{{LEGAL_REP_NAME}}
{{LEGAL_REP_ID}}
{{CITY}}
{{CREDIT_LIMIT}}
{{GENERATION_DATE}}
{{CONTRACT_ID}}
```

---

### FR-4: Legal Review Workflow (Optional but Recommended)
**Priority:** Medium

**Description:** Review step where Legal can verify generated contracts before Operations proceeds.

**User Story:** As a Legal team member, I want to quickly review auto-generated contracts to ensure accuracy, taking 2 minutes instead of 15 minutes to create them manually.

**Acceptance Criteria:**
- [ ] Configurable flag: "Require Legal Review" (on/off)
- [ ] When enabled, contract goes to Legal review queue
- [ ] Legal receives slack notification of pending review
- [ ] Legal can approve or reject with comments
- [ ] If approved, Operations notified to proceed
- [ ] If rejected, Operations notified with rejection reason
- [ ] Review SLA tracking (target: < 2 hours)

---

### FR-5: Audit Trail and Logging
**Priority:** High

**Description:** Complete audit trail of all contract generations for compliance.

**Acceptance Criteria:**
- [ ] Log every contract generation with:
  - Timestamp
  - User who generated
  - Client NIT/name
  - Contract ID
  - Data snapshot used
  - PDF file reference
- [ ] Legal team can view generation history
- [ ] Export audit logs to CSV
- [ ] Retention: minimum 7 years (legal compliance)

---
### Integration Points
1. **Finkargo Platform Database** (read-only)
   - Client data retrieval
   - Authentication (Supabase Auth)

2. **Slack** (optional for notifications)
   - Review request notifications to Legal
   - Approval/rejection notifications to Operations

3. **Future Integration** (not MVP):
   - DocuSign API for automatic upload
   - Platform API for attaching generated PDFs

---

## User Roles and Permissions

### Operations Team
- **Access:** Full access to contract generation
- **Permissions:**
  - Search clients
  - Generate contracts
  - Download PDFs
  - View generation history

### Legal Team (Sofia + team)
- **Access:** Full access + admin capabilities
- **Permissions:**
  - All Operations permissions PLUS:
  - Review contracts (if review workflow enabled)
  - Manage templates
  - View complete audit logs
  - Export reports

### Admin (VP Product / Technical Team)
- **Access:** System administration
- **Permissions:**
  - User management
  - System configuration
  - Database access
  - Deployment management

---

## Data Model

### Client Data (Read from Platform)
```typescript
interface ClientData {
  nit: string;                    // Tax ID
  nombre_importador: string;      // Company name
  representante_legal: string;    // Legal rep name
  cedula_representante: string;   // Legal rep ID
  ciudad_domicilio: string;       // City
  cupo_plataforma: number;        // Credit limit
}
```

### Contract Generation Record (Application DB)
```typescript
interface ContractGeneration {
  id: string;                     // UUID
  contract_id: string;            // Business ID (e.g., ACT-2025-001)
  client_nit: string;             // Foreign key to client
  generated_by: string;           // User ID
  generated_at: timestamp;        // Creation time
  status: 'generated' | 'under_review' | 'approved' | 'rejected';
  reviewed_by?: string;           // Legal reviewer ID
  reviewed_at?: timestamp;        // Review time
  review_notes?: string;          // Rejection reason or comments
  pdf_url: string;                // Storage path
  template_version: string;       // Template version used
  data_snapshot: JSON;            // Client data at generation time
}
```

### Contract Template
```typescript
interface ContractTemplate {
  id: string;                     // UUID
  version: string;                // Semantic version (1.0.0)
  contract_type: 'activos';       // Type identifier
  template_content: string;       // Template with placeholders
  active: boolean;                // Current active version
  created_by: string;             // User who uploaded
  created_at: timestamp;          // Upload time
  notes?: string;                 // Version notes
}
```

---

## UI/UX Requirements

### Main Screen: Contract Generation
**Layout Components:**
1. **Search Section**
   - Search input: "Buscar cliente por NIT o nombre"
   - Search button
   - Results table with client matching results

2. **Client Details Preview**
   - Card showing all client data retrieved
   - "Verificar datos" button to confirm accuracy
   - Edit capability (if data incorrect - flags for platform update)

3. **Contract Preview**
   - Read-only preview of populated contract
   - "Descargar PDF" button
   - "Generar Contrato" button (final action)

4. **History Section**
   - Recent contracts generated
   - Filter by date, client, user
   - Download previously generated contracts

### Design System (Finkargo Brand)
- Colors: Primary blue (#3C47D3), Coral CTA (#EB8774)
- Typography: Epilogue font
- Components: Material-UI with 8px border radius
- Responsive: Mobile, tablet, desktop support

---

## Success Metrics

### Primary KPIs
- **Time Savings:** 15 minutes → < 1 minute per contract
- **Daily Volume:** Support 3-15 contracts/day without Legal bottleneck
- **Legal Team Capacity:** Free up 45-225 minutes/day for Legal team
- **Process Speed:** Reduce payment release time by 30-60 minutes average

### Secondary Metrics
- User satisfaction (Operations and Legal teams)
- Error rate in generated contracts
- Platform data accuracy validation
- Number of contracts requiring Legal review (if enabled)

---

## Risks and Mitigation

### Risk 1: Platform Data Access
**Risk:** Limited or restricted access to Finkargo platform database
**Mitigation:** 
- Coordinate with platform team for read-only credentials
- Alternative: Create API endpoint on main platform if direct DB access not possible

### Risk 2: Template Legal Compliance
**Risk:** Auto-generated contracts might not meet legal standards
**Mitigation:** 
- Include Legal review workflow in MVP
- Comprehensive testing with Sofia before going live
- Version control for template updates

### Risk 3: Data Accuracy
**Risk:** Platform data might be incomplete or incorrect
**Mitigation:** 
- Validation checks before generation
- Preview step for user verification
- Flag missing/invalid data with clear error messages

--

## Dependencies

### Internal Dependencies
- Supabase project access and credentials
- Finkargo platform database end point
- Access to current Word template from Sofia
- Operations team availability for testing

### External Dependencies
- Vercel deployment account
- Render deployment account
- PDF generation library selection
- Slack Integration (for notifications)


## Appendix: Key Quotes from Transcript

> "Yo por día estoy haciendo por tres o cuatro por día bajito, no hay un día en que no haga, por día hago 3 y 4, hay días que hecho 15."
> 
> — Sofia, describing daily volume

> "El contrato es un template. Yo tengo que llenar los espacios del template... Yo entro a la plataforma, yo tengo el template en Word con los espacios en blanco, entro a la plataforma y literalmente escribo en los espacios en blanco."
> 
> — Sofia, describing current manual process

> "Necesito todo para descongestionar, como para darle respuesta más rápido a ellos y que no esté retrasado por Legal."
> 
> — Sofia, on urgency and pain points

---

**Document Status:** Requirements extracted and ready for implementation  
**Next Review:** After Sofia provides template and screen recording  
**Estimated Development Time:** 2-4 weeks to operational prototype  
**Created:** October 4, 2025  
**Version:** 1.0