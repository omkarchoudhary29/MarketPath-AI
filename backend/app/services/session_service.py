import datetime
import uuid
from typing import Optional, Tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.security import generate_session_token, hash_session_token
from backend.app.models.session import UserSession


class SessionService:
    """Manages database-backed sessions with cryptographic token hashing and instant revocation."""

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
        session_type: str = "real",
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        expires_in_seconds: int = 86400 * 7,
    ) -> Tuple[UserSession, str]:
        """Creates a new database-backed session, returning the session model and secret raw token."""
        raw_token = generate_session_token()
        token_hash = hash_session_token(raw_token)
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(seconds=expires_in_seconds)

        session = UserSession(
            id=uuid.uuid4(),
            user_id=user_id,
            organization_id=organization_id,
            token_hash=token_hash,
            session_type=session_type,
            device_info=device_info,
            ip_address=ip_address,
            is_active=True,
            created_at=now,
            last_activity_at=now,
            expires_at=expires_at,
            revoked_at=None,
        )
        db.add(session)
        await db.flush()
        return session, raw_token

    @staticmethod
    async def get_session_by_token(
        db: AsyncSession,
        raw_token: str,
    ) -> Optional[UserSession]:
        """Retrieves and validates an active session by raw token. Updates last_activity_at if valid."""
        if not raw_token:
            return None

        token_hash = hash_session_token(raw_token)
        result = await db.execute(
            select(UserSession)
            .options(selectinload(UserSession.user), selectinload(UserSession.organization))
            .where(
                UserSession.token_hash == token_hash,
                UserSession.is_active == True,
                UserSession.revoked_at == None,
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        now = datetime.datetime.now(datetime.timezone.utc)
        # Check expiration
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)

        if expires_at <= now:
            session.is_active = False
            session.revoked_at = now
            await db.commit()
            return None

        # Update activity timestamp
        session.last_activity_at = now
        await db.commit()
        return session

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        raw_token: str,
    ) -> bool:
        """Revokes an active session immediately."""
        if not raw_token:
            return False

        token_hash = hash_session_token(raw_token)
        now = datetime.datetime.now(datetime.timezone.utc)
        result = await db.execute(
            update(UserSession)
            .where(UserSession.token_hash == token_hash, UserSession.is_active == True)
            .values(is_active=False, revoked_at=now)
        )
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def revoke_all_user_sessions(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> int:
        """Revokes all active sessions for a user across all devices."""
        now = datetime.datetime.now(datetime.timezone.utc)
        result = await db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.is_active == True)
            .values(is_active=False, revoked_at=now)
        )
        await db.commit()
        return result.rowcount
