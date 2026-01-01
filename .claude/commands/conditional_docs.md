# Conditional Documentation Guide

This prompt helps you determine what documentation you should read based on the specific changes you need to make in the codebase. Review the conditions below and read the relevant documentation before proceeding with your task.

## Instructions
- Review the task you've been asked to perform
- Check each documentation path in the Conditional Documentation section
- For each path, evaluate if any of the listed conditions apply to your task
  - IMPORTANT: Only read the documentation if any one of the conditions match your task
- IMPORTANT: You don't want to excessively read documentation. Only read the documentation if it's relevant to your task.

## Conditional Documentation

- README.md
  - Conditions:
    - When operating on anything under app/server
    - When operating on anything under app/client
    - When first understanding the project structure
    - When you want to learn the commands to start or stop the server or client

- app/client/src/style.css
  - Conditions:
    - When you need to make changes to the client's style

- .claude/commands/classify_adw.md
  - Conditions:
    - When adding or removing new `adws/adw_*.py` files

- adws/README.md
  - Conditions:
    - When you're operating in the `adws/` directory

- app_docs/feature-fefa5443-fraud-detection-risk-module.md
  - Conditions:
    - When working with fraud detection or risk assessment features
    - When implementing or modifying the Risk department pages
    - When working with risk_analyst or risk_manager roles
    - When troubleshooting risk evaluation or scoring issues
    - When modifying blacklist or alert functionality

- app_docs/feature-ec3ddef5-fraud-risk-module-fixes.md
  - Conditions:
    - When working with email chain validation or NIT normalization
    - When troubleshooting Pydantic validation errors in risk module
    - When modifying file upload size limits for risk documents
    - When working with Colombian cellphone number filtering
    - When implementing domain validation or typosquatting detection
    - When modifying cross-validation discrepancy severity levels

- app_docs/feature-ea0d75d8-llm-email-extraction-riesgos.md
  - Conditions:
    - When working with AI/LLM-powered entity extraction in the Riesgos module
    - When modifying or troubleshooting OpenAI integration for email parsing
    - When working with risk_settings or AI extraction toggle
    - When implementing entity extraction from email chains (company names, NITs, representatives)
    - When troubleshooting extraction_method or ai_assisted tracking
    - When adding new settings to the risk module

- app_docs/feature-550a54d1-pa-report-classification.md
  - Conditions:
    - When working with PA (Patrimonio Autonomo) report classification
    - When implementing or modifying Finance module PA features
    - When working with pa_account_catalog, pa_classification_rules, or related tables
    - When implementing NetSuite file processing for PA accounts
    - When troubleshooting PA classification or homologation logic
    - When working with finance_admin role or PA-related RBAC

- app_docs/feature-b0a5e4a8-contador-revisor-fiscal-validation.md
  - Conditions:
    - When working with contador or revisor fiscal validation
    - When implementing signatory verification in financial statements
    - When modifying cross-validation logic for professional credentials
    - When working with Certificado de Existencia extraction fields
    - When troubleshooting financial statement signatory mismatches

- app_docs/feature-6a9aabdc-discrepancy-validation-checkboxes.md
  - Conditions:
    - When working with discrepancy validation in the Riesgos module
    - When implementing mesa de control approval workflows
    - When modifying FKCrossValidationResults or FKVerificationStatusCard components
    - When working with discrepancy_validations table or DiscrepancyValidationRepository
    - When updating cross-validation PDF export with validation status

- app_docs/feature-584b6bdd-external-communication-validation-comments.md
  - Conditions:
    - When working with email chain validation in the Riesgos module
    - When implementing external contact alert validation
    - When modifying FKEmailChainUploader or FKExternalContactTab components
    - When working with email_chain_discrepancy_validations or external_contact_validations tables
    - When extending PDF export with external communication validation data
    - When troubleshooting mesa de control validation workflows for external communications