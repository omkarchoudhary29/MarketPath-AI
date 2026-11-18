"""API Router for In-App AI Support Chatbot."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.services.support_bot_service import (
    ChatQueryRequest,
    ChatQueryResponse,
    PublicChatQueryRequest,
    PublicChatQueryResponse,
    SupportBotService,
)

router = APIRouter()


@router.post("/public-chat", response_model=PublicChatQueryResponse)
async def query_public_support_bot(
    payload: PublicChatQueryRequest,
):
    """Answers visitor and prospect queries with strict zero-access to private tenant records."""
    return await SupportBotService.answer_public_query(req=payload)



@router.post("/chat", response_model=ChatQueryResponse)
async def query_support_bot(
    payload: ChatQueryRequest,
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Answers seller queries using runtime tenant context and diagnostic tools."""
    return await SupportBotService.answer_query(
        db=db,
        organization_id=context.organization_id,
        user_email=context.user.email if hasattr(context.user, "email") else "seller@marketpath.in",
        user_role=context.role,
        req=payload,
        user_id=context.user.id if hasattr(context.user, "id") else None,
    )


@router.get("/chat/history")
async def get_support_chat_history(
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves persistent, database-backed conversation history for the authenticated user and organization."""
    messages = await SupportBotService.get_conversation_messages(
        db=db,
        user_id=context.user.id,
        organization_id=context.organization_id,
    )
    return {"messages": messages}


@router.delete("/chat/history")
async def clear_support_chat_history(
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Resets the active conversation thread for the authenticated user in this workspace."""
    success = await SupportBotService.clear_conversation_history(
        db=db,
        user_id=context.user.id,
        organization_id=context.organization_id,
    )
    return {"success": success}


@router.get("/conversations")
async def list_support_topics(
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
):
    """Returns contextual diagnostic topics and active support guidelines for the seller workspace."""
    return {
        "organization_id": str(context.organization_id),
        "recommended_topics": [
            {"title": "Diagnose Amazon SP-API Attribute Rejections", "query": "Why did my Amazon listing fail?"},
            {"title": "Check Flipkart Legal Metrology Requirements", "query": "Why is Flipkart missing attributes?"},
            {"title": "Master Inventory Decrement and Multi-Channel Sync", "query": "How does inventory sync work?"},
            {"title": "Connect Shopify Storefront via GraphQL", "query": "How do I connect Shopify?"},
            {"title": "Agency Connect RFP Workflow", "query": "How do I request agency proposals?"},
        ],
        "guardrail_status": "active",
        "consequential_action_policy": "human_confirmation_required",
    }
