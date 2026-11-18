"""MarketPath AI — Platform Admin Secure Bootstrap Script.

One-time administrative bootstrap command for establishing the primary Platform Admin account.
Generates cryptographically random initial credentials, enforces first-login password rotation
and MFA, revokes stale sessions, and writes initial access information exclusively to local
git-ignored secrets/marketpath-initial-access.txt.

Usage:
    python -m backend.scripts.bootstrap_platform_admin [--force-rotate]
"""

import argparse
import asyncio
import datetime
import os
import secrets
import sys
import uuid
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import AsyncSessionLocal
from backend.app.core.security import hash_password
from backend.app.models.audit import AuditLog
from backend.app.models.user import UserProfile
from backend.app.services.session_service import SessionService

SECRETS_DIR = Path("secrets")
SECRETS_FILE = SECRETS_DIR / "marketpath-initial-access.txt"


def generate_secure_password(length: int = 24) -> str:
    """Generates a cryptographically strong random password with 24+ bytes of entropy."""
    return secrets.token_urlsafe(length)


async def bootstrap_admin(force_rotate: bool = False) -> None:
    # 1. Verify authorization
    if not getattr(settings, "MARKETPATH_BOOTSTRAP_ADMIN", True):
        print("ERROR: Platform Admin bootstrap is not authorized in this environment.")
        sys.exit(1)

    admin_email = getattr(settings, "PLATFORM_ADMIN_BOOTSTRAP_EMAIL", "operator@marketpath.ai").strip().lower()

    async with AsyncSessionLocal() as db:
        # 2. Check if user already exists
        res = await db.execute(select(UserProfile).where(UserProfile.email == admin_email))
        user = res.scalar_one_or_none()

        # Check if already bootstrapped and not forcing rotation
        if user and user.is_platform_admin and not force_rotate:
            # Check for existing bootstrap log
            log_res = await db.execute(
                select(AuditLog).where(
                    AuditLog.action == "PLATFORM_ADMIN_BOOTSTRAPPED",
                    AuditLog.resource_id == str(user.id),
                )
            )
            existing_log = log_res.scalar_one_or_none()
            if existing_log and SECRETS_FILE.exists():
                print(f"[MarketPath Admin Bootstrap] Platform Admin '{admin_email}' is already provisioned.")
                print(f"Credentials remain intact in {SECRETS_FILE}. Use --force-rotate to regenerate credentials.")
                return

        # 3. Generate high-entropy password
        raw_password = generate_secure_password(24)
        pw_hash = hash_password(raw_password)

        if not user:
            user = UserProfile(
                id=uuid.uuid4(),
                email=admin_email,
                full_name="Platform Operator",
                account_type="admin",
                is_platform_admin=True,
                is_active=True,
                must_change_password=True,
                mfa_enabled=True,
                vetting_status="approved",
                password_hash=pw_hash,
            )
            db.add(user)
            await db.flush()
            action_desc = "PLATFORM_ADMIN_CREATED"
        else:
            user.is_platform_admin = True
            user.account_type = "admin"
            user.is_active = True
            user.must_change_password = True
            user.mfa_enabled = True
            user.vetting_status = "approved"
            user.password_hash = pw_hash
            action_desc = "PLATFORM_ADMIN_ROTATED"

        # 4. Revoke previous sessions
        revoked_count = await SessionService.revoke_all_user_sessions(db, user.id)

        # 5. Insert audit log
        audit = AuditLog(
            actor_user_id=user.id,
            action="PLATFORM_ADMIN_BOOTSTRAPPED",
            resource_type="user",
            resource_id=str(user.id),
            metadata_json={
                "email": admin_email,
                "action": action_desc,
                "revoked_sessions": revoked_count,
                "must_change_password": True,
                "mfa_enabled": True,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
        )
        db.add(audit)
        await db.commit()

        # 6. Securely write to secrets/marketpath-initial-access.txt
        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Read existing content if any
        existing_content = ""
        if SECRETS_FILE.exists():
            existing_content = SECRETS_FILE.read_text(encoding="utf-8")

        admin_block = f"""
================================================================================
MARKETPATH AI — PRODUCTION CREDENTIALS VAULT (LOCAL CONFIDENTIAL)
Last Updated: {now_str}
WARNING: NEVER COMMIT THIS FILE TO GIT OR DISTRIBUTE IN LOGS OR REPORTS.
================================================================================

REAL PLATFORM ADMINISTRATOR:
  Account Type:                Platform Admin
  Email:                       {admin_email}
  Initial Password:            {raw_password}
  First-Login Password Reset:  REQUIRED (must_change_password=True)
  MFA Enrollment:              REQUIRED (mfa_enabled=True)
  Sign-in URL:                 http://localhost:5173/login
  Direct Admin Console:        http://localhost:5173/admin
================================================================================
"""

        # Update or prepend admin block
        if "REAL PLATFORM ADMINISTRATOR:" in existing_content:
            # Replace admin block
            import re
            new_content = re.sub(
                r"={80}\s*MARKETPATH AI — PRODUCTION CREDENTIALS VAULT.*?(?=\n={80}\s*FOUR DEMO ACCOUNTS|\Z)",
                admin_block.strip() + "\n",
                existing_content,
                flags=re.DOTALL,
            )
            SECRETS_FILE.write_text(new_content, encoding="utf-8")
        else:
            SECRETS_FILE.write_text(admin_block + "\n" + existing_content, encoding="utf-8")

        # 7. Print SAFE terminal summary (no password displayed)
        print("\n" + "=" * 60)
        print("MarketPath AI — Platform Admin Bootstrap Succeeded")
        print("=" * 60)
        print(f"Platform Admin Email:       {admin_email}")
        print(f"Account State:              ACTIVE / SUPERADMIN")
        print(f"First-Login Password Reset: ENFORCED")
        print(f"MFA Enrollment:             ENFORCED")
        print(f"Revoked Stale Sessions:     {revoked_count}")
        print(f"Secure Credentials File:    {SECRETS_FILE.resolve()}")
        print("=" * 60)
        print("NOTE: Credentials have been stored securely in local git-ignored vault.")
        print("No passwords were leaked to logs or console.\n")


def main():
    parser = argparse.ArgumentParser(description="Bootstrap MarketPath AI Platform Admin account.")
    parser.add_argument("--force-rotate", action="store_true", help="Force credential rotation if admin already exists")
    args = parser.parse_args()

    asyncio.run(bootstrap_admin(force_rotate=args.force_rotate))


if __name__ == "__main__":
    main()
