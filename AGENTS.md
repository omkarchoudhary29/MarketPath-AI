# MarketPath AI — Workspace Rules & Guidelines

These workspace rules apply unconditionally to all pair-programming and agent tasks within MarketPath AI.

Full detailed rules: [`.agents/rules/marketpath-project.md`](file:///c:/Users/mukesh/Documents/Gen%20ai/LLM%20mini%20projects/marketplace/.agents/rules/marketpath-project.md)

## Core Non-Negotiables

1. **Product Truth:** MarketPath AI is a real, potentially commercial SaaS platform for emerging Indian D2C brands. Follow [`README.md`](file:///c:/Users/mukesh/Documents/Gen%20ai/LLM%20mini%20projects/marketplace/README.md) as the source of truth.
2. **Strict No-Faking Policy:** Never fake or simulate third-party connections, publishing results, ad launches, or payments. Disconnected or unapproved channels must clearly show the setup state.
3. **Tenant Security:** Enforce organization-level tenant isolation on every private database entity via `TenantContext`. All private routes must check `X-Organization-Id`.
4. **Token Encryption:** All external platform tokens stored in the database must be encrypted with AES-256-GCM.
5. **No Secrets in Frontend or Git:** Secrets stay server-side. Never commit `.env` or sensitive API keys.
6. **Master Catalogue Integrity:** Master product specs are the truth; channel overrides remain separate.
7. **Human Approval:** Publishing and campaign launches strictly require seller review and approval.
8. **Verification Requirement:** Run `python -m pytest backend/tests -v` and `npm --prefix frontend run build` after changes to verify zero regressions.

