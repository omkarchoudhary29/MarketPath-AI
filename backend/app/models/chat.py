import uuid
from typing import TYPE_CHECKING, List, Optional, Any
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import JSON

from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.user import UserProfile
    from backend.app.models.organization import Organization


class AIConversation(Base, TimestampMixin):
    """Persistent, database-backed AI Assistant conversation thread scoped to a user and organization."""
    __tablename__ = "ai_conversations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="Operational AI Diagnostics", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    messages: Mapped[List["AIChatMessage"]] = relationship(
        "AIChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AIChatMessage.created_at"
    )

    def __repr__(self) -> str:
        return f"<AIConversation(id={self.id}, user_id={self.user_id}, title={self.title})>"


class AIChatMessage(Base, TimestampMixin):
    """Individual message stored persistently in an AI conversation."""
    __tablename__ = "ai_chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' | 'bot'
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_actions: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    diagnosed_issues: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    data_sources: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    conversation: Mapped["AIConversation"] = relationship("AIConversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<AIChatMessage(id={self.id}, conversation_id={self.conversation_id}, sender={self.sender})>"
