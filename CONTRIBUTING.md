# Contributing to MarketPath AI

Thank you for your interest in contributing to **MarketPath AI** — an AI-powered D2C omnichannel commerce operating platform designed for modern Indian and global brands.

---

## 1. Development Principles & Non-Negotiables

Before writing code, review [AGENTS.md](AGENTS.md) and the system architecture in [README.md](README.md#6-system-architecture). Our core engineering non-negotiables are:

1. **Strict No-Faking Policy**: Real platform connectors (Shopify, Amazon, Flipkart, WooCommerce, etc.) must reflect actual connection states. Disconnected or unapproved channels must clearly show setup requirements.
2. **Tenant Isolation**: Every database operation on merchant data must enforce `TenantContext` isolation. Cross-tenant leakage is strictly unacceptable.
3. **Cryptographic Protection**: All external API credentials and secrets stored in the database must be encrypted with AES-256-GCM.
4. **Human-in-the-Loop Safeguards**: Generative AI assistants may draft, prepare, or propose changes, but destructive mutations (e.g., catalog deletions, price edits, marketplace broadcasting) mandate explicit merchant review and approval.
5. **Option C Design System**: All UI components must adhere to the warm, professional Option C palette (`#08765B` primary green, `#075443` deep forest, `#FCFBF7` warm background, `#E5EAE6` borders).

---

## 2. Local Development Setup

### Prerequisites
- **Python**: 3.11 or 3.12
- **Node.js**: 20+ (with npm 10+)
- **Git**

### Step-by-Step Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/omkarchoudhary29/marketpath-ai.git
   cd marketpath-ai
   ```

2. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   For local development with SQLite, the defaults in `.env.example` work out of the box without external services.

3. **Backend Setup**:
   ```bash
   # Create virtual environment
   python -m venv .venv
   # On Windows: .venv\Scripts\activate
   # On macOS/Linux: source .venv/bin/activate

   # Install dependencies
   pip install -r backend/requirements.txt

   # Seed demo database
   python -m backend.scripts.seed_demo --force

   # Start FastAPI development server
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` to access the application.

---

## 3. Pre-Commit Verification Suite

Before submitting a pull request, run the complete verification suite locally:

```bash
# 1. Run all backend unit & integration tests
python -m pytest backend/tests -v

# 2. Verify deterministic demo dataset
python -m backend.scripts.verify_demo_data

# 3. Compile and build the frontend bundle
cd frontend && npm run build
```

---

## 4. Pull Request Workflow

1. Create a dedicated topic branch:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bugfix-name
   ```
2. Make atomic, well-documented commits.
3. Keep pull requests focused on a single concern.
4. Fill out the pull request template completely.
5. Ensure CI checks pass on GitHub Actions.

---

## 5. Reporting Issues

Please submit bug reports and feature proposals using the official [GitHub Issue Templates](.github/ISSUE_TEMPLATE/).
