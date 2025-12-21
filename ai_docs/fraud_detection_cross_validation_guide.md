# Fraud Detection Cross-Validation Guide for Credit Line Applications

## Document Analysis: Azelis Colombia Fraud Case

Based on the analysis of the provided documents from the Azelis fraud case, this guide outlines comprehensive cross-validation checks to detect potential document tampering and fraud in credit line applications.

## Key Documents Analyzed

1. **Financial Statements** (2024 EEFF AZELIS, parcial 2025AZELIS EEFF)
2. **ID Document** (CC Repre Rocsa Colombia)
3. **Tax Registration (RUT)** (RUT AZELIS COLOMBIA SAS)
4. **Shareholder Composition** (composicion accionaria AZELIS COLOMBIA SAS)

## Critical Cross-Validation Points

### 1. Company Name and Legal Entity Consistency

**What to check:**
- Exact company name matching across ALL documents
- Legal entity type consistency (S.A.S., S.A., LTDA, etc.)

**Red flags identified:**
- Financial statements show "AZELIS COLOMBIA S.A.S."
- ID document shows association with "ROCSA COLOMBIA S A" (different company, different entity type)
- This mismatch indicates potential document manipulation

**Automated validation:**
- Extract company name from each document
- Perform exact string matching
- Flag any variations in:
  - Company name spelling
  - Legal entity designation
  - Use of periods, spaces, or punctuation

### 2. Tax ID (NIT) Verification

**What to check:**
- NIT consistency across all documents
- NIT format validation (XXX.XXX.XXX-X)
- Verification digit calculation

**Documents containing NIT:**
- RUT: 830.027.231-3
- Financial statements: 830.027.231-3
- All other documents should reference the same NIT

**Automated validation:**
- Extract NIT from all documents
- Verify format and verification digit
- Cross-reference with official DIAN database (if available)
- Flag any NIT mismatches

### 3. Representative/Signatory Validation

**What to check:**
- Legal representative name consistency
- ID number matching across documents
- Signature consistency

**Red flags identified:**
- ID document shows: Daniel Abad Fajardo González (CC 79.908.064)
- Financial statements signed by: Daniel Abad Fajardo Gonzáles, Aida Elena Granda Gallego
- Shareholder composition shows: Daniel Abad Fajardo González with 82% ownership

**Automated validation:**
- Extract signatory names and ID numbers
- Verify consistency in:
  - Name spelling (note: Gonzáles vs González)
  - ID numbers
  - Titles and positions

### 4. Email Domain Verification

**What to check:**
- Email domains used in documents
- Domain existence and ownership
- Domain age and registration details

**From meeting transcript:**
- Legitimate domain: acelis.com
- Fraudulent domain: acelis.com.co

**Automated validation:**
- Extract all email addresses from documents
- Verify domain registration (WHOIS lookup)
- Check domain age (newly registered domains are suspicious)
- Compare with company's official website domain

### 5. Financial Statement Integrity

**What to check:**
- Auditor information consistency
- Financial figures logical progression
- Signature and stamp authenticity
- Document metadata

**Key validations:**
- Both statements claim PricewaterhouseCoopers (PwC) audit
- Verify auditor license numbers: T-291064-T (contador)
- Check for image manipulation in signatures/stamps
- Validate financial ratios and year-over-year changes

**Automated validation:**
- OCR extraction of auditor information
- Cross-reference auditor license numbers with professional databases
- Analyze document metadata for editing timestamps
- Calculate and verify financial ratios

### 6. Address and Location Consistency

**What to check:**
- Registered address matching across documents
- Physical location validation
- Phone numbers and contact information

**Documents show:**
- RUT: PAR IND LOGIKA II AUT MEDELLIN COSTADO SUR KM 5 7 BG 1, Tenjo, Cundinamarca
- Consistent across analyzed documents

**Automated validation:**
- Extract and standardize addresses
- Geocode validation
- Cross-reference with Google Maps/business directories

### 7. Document Dates and Timeline Logic

**What to check:**
- Document issuance dates
- Logical timeline progression
- Recent updates or modifications

**Key dates identified:**
- Financial statements: December 31, 2024 (issued February 18, 2025)
- Shareholder composition: August 10, 2025
- ID document: Issued June 27, 1995

**Automated validation:**
- Extract all dates from documents
- Verify chronological logic
- Flag documents with future dates or illogical sequences

### 8. Shareholder and Ownership Verification

**What to check:**
- Shareholder names and percentages
- Total ownership adds to 100%
- Cross-reference with other corporate documents

**Analysis shows:**
- Shareholder document lists 7 shareholders
- Daniel Abad Fajardo González: 82% (majority owner)
- Total shares: 470,857 at $10,000 COP each

**Automated validation:**
- Sum ownership percentages (must equal 100%)
- Verify share calculations
- Cross-reference major shareholders with signatory authority

### 9. Banking Information Validation

**What to check:**
- Bank account ownership
- Bank name consistency
- Account status verification

**From meeting notes:**
- Fraudulent banking certificates from Bank of America
- Domain mismatch in bank communications

**Automated validation:**
- Extract bank names and account numbers
- Verify bank domain in email communications
- Request direct bank verification for large credit lines

### 10. Professional Registration Numbers

**What to check:**
- Accountant professional card numbers
- Auditor registration validity
- Chamber of Commerce registration

**Key numbers:**
- Accountant: Tarjeta Profesional 97947-T
- Auditor: Various T-numbers listed

**Automated validation:**
- Extract professional registration numbers
- Verify with professional boards
- Check for expired or suspended licenses

## Implementation Recommendations

### Immediate Actions

1. **Automated Document Parser**
   - Implement OCR with high accuracy for Spanish documents
   - Extract key fields: Company name, NIT, emails, addresses, dates, signatures
   - Store extracted data in structured format for cross-validation

2. **Validation Rules Engine**
   - Create rules for each cross-validation point
   - Assign risk scores to each mismatch
   - Generate automated alerts for high-risk applications

3. **External Data Integration**
   - DIAN database for NIT verification
   - Professional board APIs for license verification
   - Domain registration services for email validation
   - Google Maps API for address verification

### Risk Scoring Matrix

| Check Type | Weight | Critical Mismatch Score |
|------------|--------|------------------------|
| Company Name | 25% | 100 (immediate flag) |
| NIT Consistency | 20% | 100 (immediate flag) |
| Email Domain | 15% | 80 |
| Representative ID | 15% | 90 |
| Financial Integrity | 10% | 70 |
| Address Consistency | 5% | 50 |
| Date Logic | 5% | 60 |
| Professional Numbers | 5% | 70 |

### Workflow Integration

1. **Document Upload Phase**
   - Require specific document types
   - Implement file type and size validation
   - Check for image manipulation indicators

2. **Automated Analysis Phase**
   - Run OCR extraction
   - Execute cross-validation rules
   - Generate risk score

3. **Manual Review Phase**
   - Flag applications with risk score > 60
   - Require additional verification for scores > 80
   - Automatic rejection for scores = 100

4. **Verification Phase**
   - Direct chamber of commerce download
   - Bank verification calls
   - Site visits for large credit lines

## Lessons from the Azelis Case

1. **Mixed Legitimate and Fake Documents**: Fraudsters used real Chamber of Commerce and RUT documents as a foundation, building fake documents around them.

2. **Sophisticated Forgery**: Financial statements appeared professionally done, supposedly audited by PwC, making visual detection difficult.

3. **Small Details Matter**: The fraud was initially detected due to spelling errors in communications, highlighting the importance of analyzing all customer interactions.

4. **Domain Spoofing**: Creating similar-looking domains (acelis.com vs acelis.com.co) is a common tactic.

5. **Identity Theft**: Using real person's data with replaced photos in ID documents.

## Continuous Improvement

1. **Machine Learning Integration**
   - Train models on known fraud cases
   - Identify new patterns automatically
   - Improve OCR accuracy for document extraction

2. **Regular Updates**
   - Update validation rules based on new fraud attempts
   - Refresh external data source integrations
   - Review and adjust risk scoring weights

3. **Audit Trail**
   - Log all validation checks performed
   - Document manual override decisions
   - Maintain evidence for regulatory compliance

## Conclusion

The Azelis fraud case demonstrates the sophistication of modern financial fraud attempts. By implementing comprehensive cross-validation checks across multiple data points, organizations can significantly reduce their exposure to fraud risk. The key is to make it difficult for fraudsters to maintain consistency across all required documents while making the legitimate application process as smooth as possible.

Remember: No single check is foolproof, but the combination of multiple validation points creates a robust defense against fraud.