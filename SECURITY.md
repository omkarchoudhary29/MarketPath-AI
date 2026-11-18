# Security Policy — MarketPath AI

MarketPath AI takes security, data privacy, and tenant isolation seriously. This document outlines our vulnerability disclosure policy and core security safeguards.

---

## Supported Versions

Only the latest release on the `main` branch receives active security updates and patches.

| Version / Branch | Supported |
|------------------|-----------|
| `main`           | :white_check_mark: |
| Legacy tags      | :x:       |

---

## Reporting a Vulnerability

If you believe you have discovered a security vulnerability in MarketPath AI, please disclose it responsibly.

**DO NOT open a public GitHub issue for security vulnerabilities.**

Instead, please send an encrypted or private email with the subject `[SECURITY REPORT] MarketPath AI` to:
- **Email:** `security@marketpath.ai` (or via private repository security advisory on GitHub)

### What to Include in Your Report
1. Detailed description of the vulnerability.
2. Step-by-step reproduction instructions or a minimal proof-of-concept (PoC).
3. The potential impact of the vulnerability (e.g., cross-tenant data access, privilege escalation).
4. Any proposed remediations or patches, if available.

### Response Timeline
- **Initial Acknowledgement:** Within 48 hours of receipt.
- **Triage & Assessment:** Within 5 business days.
- **Resolution & Release:** Targeted within 14 business days depending on severity.

---

## Architectural Security Safeguards

MarketPath AI is built with defense-in-depth principles:

1. **Multi-Tenant Isolation**: All tenant records enforce scoping via `TenantContext`. Cross-tenant IDOR access is tested and prevented by automated integration test suites.
2. **Cryptographic Storage of Channel Secrets**: External marketplace credentials (OAuth tokens, API keys) are encrypted at rest using AES-256-GCM authenticated encryption with unique per-record nonces.
3. **Founder PII Sanitization**: Client briefs visible to agency partners in the Agency Connect marketplace are sanitized by server-side filters to prevent leakage of personal phone numbers, emails, and direct billing accounts.
4. **Role-Based Access Control (RBAC)**: Strict segregation between Merchant, Agency, Consultant, and Platform Administrator accounts. Administrative permissions cannot be self-assigned via public signup.
5. **AI Safety & Mutation Boundaries**: Generative AI workflows cannot execute destructive or consequential actions (such as product deletions, pricing modifications, or external marketplace publishing) without explicit seller approval.

For a comprehensive technical threat model and security architecture, see [README.md](README.md#15-security--tenant-isolation).
