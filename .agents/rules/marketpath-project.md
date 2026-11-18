# MarketPath AI — Permanent Engineering Rules & Project Guidelines

> **Scope:** Project-wide rules for MarketPath AI workspace (`marketplace`).  
> **Source of Truth:** [`README.md`](file:///c:/Users/mukesh/Documents/Gen%20ai/LLM%20mini%20projects/marketplace/README.md).
> **Version:** 1.0 (Commercial Beta Hardened)

---

## 1. Product Identity & Core Positioning

- **Product Name:** MarketPath AI.
- **Category:** AI-assisted D2C commerce and growth operating platform.
- **Core Promise:** *One product catalogue. Multiple connected channels. AI-powered marketing. One control centre.*
- **Target Audience:** Emerging Indian direct-to-consumer (D2C) product brands (initially home, lifestyle, and gifting brands in Pune, Mumbai, and Maharashtra).
- **Core Value Loop:** Add a product once to the master catalogue -> Generate grounded channel content -> Preview & publish to connected channels -> Plan & manage approved ad campaigns -> View verified unified analytics -> Discover & hire vetted agencies via **MarketPath Agency Connect**.
- **Real SaaS Product:** Never treat MarketPath AI as a generic toy, student dashboard, or landing-page demo. Every button, route, filter, and state transition must be completely functional.

---

## 2. Approved Technology Stack

- **Frontend:** React 18 + Vite + TypeScript with React Router v6.
- **Styling & UI:** Tailwind CSS and Lucide React icons; accessible, high-contrast, responsive layouts.
- **Backend API:** Python 3.11+ with FastAPI.
- **Data Validation & Serialisation:** Pydantic v2 schemas (`ConfigDict(from_attributes=True)`).
- **ORM & Data Layer:** Async SQLAlchemy 2.0 (`AsyncSession`).
- **Database & Auth:** PostgreSQL 16 (hosted via Supabase in production; SQLite `marketpath.db` in local dev). Authentication powered by Supabase GoTrue JWTs.
- **Media CDN:** Cloudinary (direct client uploads signed via server-side HMAC-SHA1; credentials hidden from browser).
- **AI Engine:** Google Gemini API (`gemini-2.5-flash`), with deterministic rule-based template fallback when keys are absent or offline.
- **Cache & Queues:** Redis 7 and asynchronous job workers for decoupled publishing and sync tasks.
- **Containerisation & Deployment:** Multi-stage `Dockerfile`, `docker-compose.yml`, and `frontend/vercel.json`.

---

## 3. System Architecture & Modularity

- **Modular Monolith:** Maintain clear boundaries between domain services (`auth`, `tenancy`, `products`, `media`, `content`, `channels`, `publishing`, `campaigns`, `analytics`, `billing`, `agency`).
- **No Premature Microservices:** Retain a single unified codebase with modular separation rather than distributed microservices or Kubernetes overhead.
- **Reusable Services & Contracts:** Business logic resides in `backend/app/services/` and UI state in `frontend/src/context/`. API contracts documented in `README.md` are binding.
- **Controlled Migrations:** All database schema changes must be versioned via Alembic migrations (`backend/alembic/versions/`). Never modify database tables ad-hoc.

---

## 4. Strict Security & Tenancy Rules

- **Zero Secrets in Frontend:** Never place API secrets, service role keys, master encryption keys, or payment credentials in frontend code, Git commits, docs, or logs.
- **Tenant Isolation:** Enforce organization-level tenant isolation on every private database entity via `TenantContext`. Validate `X-Organization-Id` against verified user memberships.
- **Backend-Enforced RBAC:** Enforce role hierarchy (`Owner` > `Admin` > `Member` > `Viewer`) on all mutating and sensitive endpoints. Cost prices remain confidential to owners/admins.
- **AES-256 Token Encryption:** All external platform tokens (Shopify, Meta) stored at rest must be encrypted using AES-256-GCM via `backend.app.core.security.encrypt_token`.
- **Cryptographic Webhooks:** Verify incoming webhooks using HMAC signatures (Shopify, Meta, Razorpay, Cashfree) and prevent replay attacks via idempotency tables.
- **Audit Logging:** Maintain immutable audit records in `campaign_audit_logs` and security logs for state transitions, approvals, and credential modifications.

---

## 5. Product Integrity & No-Faking Principles

- **Master Catalogue as Source of Truth:** Master product specifications (`title`, `sku`, `price`, `description`, `attributes`) are preserved intact. Channel-specific overrides (Shopify HTML, Instagram captions) live in separate override tables.
- **Mandatory Seller Approval:** All AI-generated content, omnichannel publishing, and ad launches require explicit human confirmation. Ad budgets require hard spending caps.
- **Strict No-Faking Policy:** Never simulate or fake successful third-party connections, publishing actions, ad launches, payment captures, or analytics results. If credentials or partner approvals are absent, show the exact pending/unconnected state and provide clear setup instructions or manual export workflows.
- **Demo Data Isolation:** Mock data must be visibly tagged (`[Demo Data]` or `is_demo=True`). Real accounts must never display mixed or synthetic data.
- **Grounded AI Generation:** Prompts sent to Gemini must be grounded strictly in approved master product attributes, brand voice, and target personas. Never hallucinate product specifications.

---

## 6. Engineering Discipline & Pair-Programming Workflow

1. **Inspect Before Coding:** Inspect existing files, routes, schemas, and dependencies before introducing changes.
2. **Preserve Working Code:** Do not overwrite, break, or delete existing working modules or configurations.
3. **Follow Project Docs:** Align all implementations with `PROJECT_CONTEXT.md`, `PRD.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`, and `API_CONTRACTS.md`.
4. **Automated Verification:** Run the backend test suite (`python -m pytest backend/tests -v`) and frontend build check (`npm --prefix frontend run build`) after any code modification.
5. **Report Actual Status:** Always provide truthful, objective summaries of what was implemented, what was tested, and any known limitations.
