"""Context-Aware AI Support Chatbot Service.

Provides single, unified, context-grounded AI assistance for sellers across
the MarketPath platform. Accesses tenant-isolated runtime context (active products,
recent publishing job failures, channel integration statuses, unread notifications)
to diagnose real issues and guide the seller through operational workflows.
"""

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.models.catalogue import Product
from backend.app.models.channel import ChannelConnection, PublishingJob
from backend.app.models.notification import Notification
from backend.app.models.chat import AIConversation, AIChatMessage
from backend.app.services.gemini_service import is_gemini_configured

logger = logging.getLogger(__name__)

SENSITIVE_CREDENTIAL_PATTERNS = [
    re.compile(r"(?i)(?:password|passwd|pwd|secret|api[_-]?key|bearer|token)\s*[:=]\s*['\"]?([^\s'\"]+)"),
    re.compile(r"(?i)\b(?:marketpath123|admin123|demo123|MarketPath@\w+)\b"),
    re.compile(r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"),
    re.compile(r"\b[0-9a-fA-F]{32,64}\b"),
]


def sanitize_ai_content(text: str) -> str:
    """Removes sensitive credentials, API keys, passwords, and tokens before storing or passing to LLM."""
    if not text:
        return text
    sanitized = text
    for pattern in SENSITIVE_CREDENTIAL_PATTERNS:
        sanitized = pattern.sub("[REDACTED_CREDENTIAL]", sanitized)
    return sanitized


class ChatQueryRequest(BaseModel):
    message: str
    current_page: Optional[str] = "/app/dashboard"
    history: List[Dict[str, str]] = []


class ChatQueryResponse(BaseModel):
    answer: str
    suggested_actions: List[Dict[str, str]] = []  # e.g. [{"label": "View Failed Jobs", "action_url": "/app/publishing"}]
    diagnosed_issues: List[str] = []
    data_sources_used: List[str] = []


class PublicChatQueryRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: List[Dict[str, str]] = []


class PublicChatQueryResponse(BaseModel):
    answer: str
    suggested_actions: List[Dict[str, str]] = []
    data_sources_used: List[str] = []



class SupportBotService:
    """Diagnoses platform issues and answers user queries with strict tenant isolation."""

    @staticmethod
    async def get_tenant_support_context(db: AsyncSession, organization_id: uuid.UUID) -> Dict[str, Any]:
        """Gathers tenant operational state for prompt grounding."""
        # 1. Connected channels
        conn_res = await db.execute(
            select(ChannelConnection).where(ChannelConnection.organization_id == organization_id)
        )
        connections = conn_res.scalars().all()
        conn_summary = [
            f"- {c.channel_type.capitalize()}: status={c.status}, account={c.account_name}, last_synced={c.last_synced_at}"
            for c in connections
        ]

        # 2. Recent failed or processing publishing jobs
        jobs_res = await db.execute(
            select(PublishingJob)
            .options(selectinload(PublishingJob.attempts))
            .where(PublishingJob.organization_id == organization_id)
            .order_by(desc(PublishingJob.created_at))
            .limit(5)
        )
        jobs = jobs_res.scalars().all()
        job_summary = []
        for j in jobs:
            last_err = j.attempts[-1].error_message if j.attempts else None
            job_summary.append(
                f"- Job {j.idempotency_key}: type={j.job_type}, status={j.status}, retries={j.retry_count}, error={last_err}"
            )

        # 3. Active products count
        prod_count_res = await db.execute(
            select(Product.sku, Product.title, Product.status)
            .where(Product.organization_id == organization_id)
            .limit(8)
        )
        products = prod_count_res.all()
        prod_summary = [f"- {p[0]}: '{p[1]}' ({p[2]})" for p in products]

        # 4. Unread notifications
        notif_res = await db.execute(
            select(Notification)
            .where(Notification.organization_id == organization_id, Notification.is_read == False)
            .order_by(desc(Notification.created_at))
            .limit(5)
        )
        notifs = notif_res.scalars().all()
        notif_summary = [f"- [{n.severity.upper()}] {n.domain}: {n.title} - {n.message}" for n in notifs]

        return {
            "connections": "\n".join(conn_summary) or "No channels connected yet.",
            "recent_jobs": "\n".join(job_summary) or "No recent publishing jobs.",
            "sample_products": "\n".join(prod_summary) or "No products in catalogue.",
            "unread_notifications": "\n".join(notif_summary) or "No unread alerts.",
        }

    @staticmethod
    def _check_consequential_guardrail(query: str) -> Optional[ChatQueryResponse]:
        """Intercepts consequential or irreversible commands and requires explicit human confirmation."""
        q_lower = query.lower()
        consequential_actions = [
            ("publish", "/app/publishing", "Omnichannel Publishing Wizard", "Publishing batches require your explicit cryptographic approval snapshot under Rule 7 to ensure content accuracy and pricing safety."),
            ("delete", "/app/products", "Master Product Catalogue", "Product deletion or soft-archiving requires explicit merchant confirmation in your Master Catalogue."),
            ("disconnect", "/app/integrations", "Connected Channels", "Channel disconnection requires manual confirmation in Connected Channels. Disconnecting never deletes your Master Product records."),
            ("change price", "/app/products", "Master Product Catalogue", "Price modifications must be approved directly in your Master Catalogue or Channel Specific Overrides."),
        ]
        for trigger, action_url, action_label, explanation in consequential_actions:
            if trigger in q_lower and any(w in q_lower for w in ["now", "do it", "please", "confirm", "execute", "start", "all", "batch", "channel"]):
                return ChatQueryResponse(
                    answer=(
                        f"🛡️ **Action Guardrail Notice**:\n\n"
                        f"MarketPath AI does not autonomously execute irreversible or commercial mutations on your behalf.\n\n"
                        f"{explanation}\n\n"
                        f"You can safely review and perform this action using the button below."
                    ),
                    suggested_actions=[
                        {"label": f"Go to {action_label}", "action_url": action_url},
                    ],
                    diagnosed_issues=["Consequential action blocked without explicit seller authorization."],
                    data_sources_used=["Platform Safety & Human-in-the-Loop Governance"],
                )
        return None

    @staticmethod
    def _deterministic_answer(query: str, current_page: str, ctx: Dict[str, Any]) -> ChatQueryResponse:
        """Deterministic diagnostic engine when Gemini API is unconfigured."""
        q_lower = query.lower()

        guardrail = SupportBotService._check_consequential_guardrail(query)
        if guardrail:
            return guardrail

        # Diagnose Amazon failures
        if "amazon" in q_lower and ("fail" in q_lower or "missing" in q_lower or "error" in q_lower):
            return ChatQueryResponse(
                answer=(
                    "Amazon India listings require several mandatory attributes under SP-API and Indian Legal Metrology regulations:\n\n"
                    "1. **Package Shipping Weight & Carton Dimensions**: Required for Easy Ship and FBA freight tier calculation.\n"
                    "2. **Country of Origin**: Must be set to 'India' for domestic products.\n"
                    "3. **Standard Selling Price & Currency**: Must be positive INR.\n"
                    "4. **Product Bullet Points**: Amazon requires at least 3 descriptive bullet points.\n\n"
                    "You can fill in these missing specifications directly in your Master Catalogue or via the 7-Step Publishing Wizard."
                ),
                suggested_actions=[
                    {"label": "Review Master Catalogue", "action_url": "/app/products"},
                    {"label": "Launch Publishing Wizard", "action_url": "/app/publishing"},
                ],
                diagnosed_issues=["Missing Amazon SP-API package attributes or bullet points."],
                data_sources_used=["Channel Capability Registry (Amazon India)"],
            )

        # Diagnose Flipkart failures
        if "flipkart" in q_lower and ("fail" in q_lower or "missing" in q_lower or "attribute" in q_lower):
            return ChatQueryResponse(
                answer=(
                    "Flipkart Seller Hub enforces strict validation rules:\n\n"
                    "1. **Maximum Retail Price (MRP)**: The selling price cannot exceed MRP.\n"
                    "2. **GST HSN Code**: Mandatory for all physical goods.\n"
                    "3. **Packaging Weight & Dimensions**: Required for Ekart logistics.\n\n"
                    "Check your product's Packaging Specifications tab to ensure these fields are completed."
                ),
                suggested_actions=[
                    {"label": "Edit Product Specifications", "action_url": "/app/products"},
                ],
                diagnosed_issues=["Flipkart HSN or MRP requirement."],
                data_sources_used=["Channel Capability Registry (Flipkart)"],
            )

        # Connect Shopify
        if "shopify" in q_lower and "connect" in q_lower:
            return ChatQueryResponse(
                answer=(
                    "To connect your Shopify store:\n\n"
                    "1. Go to **Connected Channels** in your sidebar.\n"
                    "2. Under **Brand Storefronts**, click on **Shopify**.\n"
                    "3. Enter your `.myshopify.com` store domain.\n"
                    "4. Authorize MarketPath in your Shopify Admin console.\n\n"
                    "MarketPath will automatically sync your products, variants, and stock once approved."
                ),
                suggested_actions=[
                    {"label": "Go to Connected Channels", "action_url": "/app/integrations"},
                ],
                diagnosed_issues=[],
                data_sources_used=["Integration Hub Guide"],
            )

        # Inventory sync
        if "inventory" in q_lower or "stock" in q_lower or "sync" in q_lower:
            return ChatQueryResponse(
                answer=(
                    "MarketPath maintains a single master stock level for each SKU. When an order arrives on any connected "
                    "channel (Shopify, WooCommerce, Amazon, Flipkart), MarketPath automatically decrements your central inventory "
                    "and queues stock adjustment updates to all your other active channels to prevent overselling."
                ),
                suggested_actions=[
                    {"label": "View Master Products", "action_url": "/app/products"},
                    {"label": "Check Channel Health", "action_url": "/app/integrations"},
                ],
                diagnosed_issues=[],
                data_sources_used=["Order & Stock Synchronisation Engine"],
            )

        # Generic default response
        return ChatQueryResponse(
            answer=(
                f"I'm your MarketPath AI assistant! You're currently viewing {current_page}.\n\n"
                f"**Connected Channels Status:**\n{ctx.get('connections')}\n\n"
                f"**Recent Jobs:**\n{ctx.get('recent_jobs')}\n\n"
                "I can help you diagnose listing errors, complete marketplace category forms, connect storefronts, or understand your sales analytics. What would you like help with?"
            ),
            suggested_actions=[
                {"label": "Master Catalogue", "action_url": "/app/products"},
                {"label": "Publishing Hub", "action_url": "/app/publishing"},
            ],
            diagnosed_issues=[],
            data_sources_used=["Runtime Tenant State"],
        )

    @staticmethod
    async def get_or_create_active_conversation(
        db: AsyncSession,
        user_id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
    ) -> AIConversation:
        """Finds existing active AI conversation or creates a new persistent session."""
        conv_query = select(AIConversation).where(
            AIConversation.user_id == user_id,
            AIConversation.is_active == True,
        )
        if organization_id:
            conv_query = conv_query.where(
                (AIConversation.organization_id == organization_id) | (AIConversation.organization_id.is_(None))
            )
        conv_res = await db.execute(conv_query.order_by(desc(AIConversation.updated_at)).limit(1))
        conv = conv_res.scalar_one_or_none()
        if not conv:
            conv = AIConversation(
                user_id=user_id,
                organization_id=organization_id,
                title="Operational AI Diagnostics",
                is_active=True,
            )
            db.add(conv)
            await db.flush()
        return conv

    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession,
        user_id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves persistent chat messages strictly for the authenticated user and organization."""
        conv_query = select(AIConversation).where(
            AIConversation.user_id == user_id,
            AIConversation.is_active == True,
        )
        if organization_id:
            conv_query = conv_query.where(
                (AIConversation.organization_id == organization_id) | (AIConversation.organization_id.is_(None))
            )
        conv_res = await db.execute(conv_query.order_by(desc(AIConversation.updated_at)).limit(1))
        conv = conv_res.scalar_one_or_none()
        if not conv:
            return []

        msgs_res = await db.execute(
            select(AIChatMessage)
            .where(AIChatMessage.conversation_id == conv.id)
            .order_by(AIChatMessage.created_at.asc())
        )
        messages = msgs_res.scalars().all()
        return [
            {
                "id": str(m.id),
                "sender": m.sender,
                "text": m.message_text,
                "suggested_actions": m.suggested_actions or [],
                "diagnosed_issues": m.diagnosed_issues or [],
                "data_sources": m.data_sources or [],
                "timestamp": m.created_at.strftime("%I:%M %p") if m.created_at else "",
            }
            for m in messages
        ]

    @staticmethod
    async def clear_conversation_history(
        db: AsyncSession,
        user_id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """Deactivates current active conversation thread for this user so a clean thread starts."""
        conv_query = select(AIConversation).where(
            AIConversation.user_id == user_id,
            AIConversation.is_active == True,
        )
        if organization_id:
            conv_query = conv_query.where(
                (AIConversation.organization_id == organization_id) | (AIConversation.organization_id.is_(None))
            )
        conv_res = await db.execute(conv_query)
        for conv in conv_res.scalars().all():
            conv.is_active = False
        await db.commit()
        return True

    @staticmethod
    async def answer_query(
        db: AsyncSession,
        organization_id: uuid.UUID,
        user_email: str,
        user_role: str,
        req: ChatQueryRequest,
        user_id: Optional[uuid.UUID] = None,
    ) -> ChatQueryResponse:
        """Answers user question using server-side Gemini with injected tenant context and database persistence."""
        safe_message = sanitize_ai_content(req.message)

        # Retrieve or create active conversation thread if user_id is provided
        active_conv = None
        if user_id:
            active_conv = await SupportBotService.get_or_create_active_conversation(db, user_id, organization_id)
            user_msg_record = AIChatMessage(
                conversation_id=active_conv.id,
                sender="user",
                message_text=safe_message,
            )
            db.add(user_msg_record)
            await db.flush()

        ctx = await SupportBotService.get_tenant_support_context(db, organization_id)

        # Consequential action guardrail check (enforced before any model call)
        guardrail = SupportBotService._check_consequential_guardrail(safe_message)
        if guardrail:
            res = guardrail
        elif not is_gemini_configured():
            res = SupportBotService._deterministic_answer(safe_message, req.current_page or "/app/dashboard", ctx)
        else:
            system_instruction = f"""You are the MarketPath AI In-App Support Assistant for Indian D2C product brands.
Current User: {user_email} (Role: {user_role})
Active Page: {req.current_page}

RUNTIME TENANT CONTEXT (Isolated strictly to this seller's organization):
Connected Channels:
{ctx.get('connections')}

Sample Active Products:
{ctx.get('sample_products')}

Recent Publishing Tasks:
{ctx.get('recent_jobs')}

Unread Alerts:
{ctx.get('unread_notifications')}

GUIDELINES:
1. Provide concise, actionable, helpful guidance.
2. If diagnosing an error (e.g. Amazon, Flipkart, Shopify, Meta), refer to actual channel requirements (weight, HSN, MRP, white background image).
3. If the user asks consequential actions (e.g. publish, change prices, delete), advise them where to do it with explicit confirmation.
4. Output structured JSON matching ChatQueryResponse."""

            prompt = f"""Conversation history:
{req.history}

User question:
{safe_message}"""

            try:
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                resp = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt + "\n\nReturn strictly valid JSON with keys: answer (string), suggested_actions (list of {label: string, action_url: string}), diagnosed_issues (list of string), data_sources_used (list of string).",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.3,
                    ),
                )
                raw = json.loads(resp.text or "{}")
                res = ChatQueryResponse.model_validate(raw)
            except Exception as e:
                logger.warning(f"Gemini support bot query failed ({str(e)}). Falling back to deterministic diagnostics.")
                res = SupportBotService._deterministic_answer(safe_message, req.current_page or "/app/dashboard", ctx)

        # Sanitize answer text before returning or storing
        res.answer = sanitize_ai_content(res.answer)

        # Persist bot response in database
        if active_conv:
            bot_msg_record = AIChatMessage(
                conversation_id=active_conv.id,
                sender="bot",
                message_text=res.answer,
                suggested_actions=res.suggested_actions,
                diagnosed_issues=res.diagnosed_issues,
                data_sources=res.data_sources_used,
            )
            db.add(bot_msg_record)
            await db.commit()

        return res

    @staticmethod
    def _deterministic_public_answer(query: str) -> PublicChatQueryResponse:
        """Deterministic public responses with strict prohibition of private data access."""
        q_lower = query.lower()

        # Check for prohibited private data access
        private_terms = ["order", "my order", "orders", "track order", "product", "products", "stock", "inventory", "sales", "revenue", "analytics", "customer", "invoice", "payment", "bank", "account balance"]
        if any(term in q_lower for term in private_terms):
            return PublicChatQueryResponse(
                answer=(
                    "Order, product, inventory, and revenue information is available in your secure workspace after you sign in. "
                    "If you are a registered brand owner, please sign in to view your real-time operational data."
                ),
                suggested_actions=[
                    {"label": "Sign In to Workspace", "action_url": "/login"},
                    {"label": "Start Free Workspace", "action_url": "/signup"},
                ],
                data_sources_used=["Public Assistant Security Boundary"],
            )

        # Channels supported
        if "channel" in q_lower or "shopify" in q_lower or "amazon" in q_lower or "flipkart" in q_lower:
            return PublicChatQueryResponse(
                answer=(
                    "MarketPath AI supports a 4-group channel ecosystem tailored for Indian D2C brands:\n\n"
                    "1. **Storefronts**: Shopify (Live Admin GraphQL) and WooCommerce (REST v3).\n"
                    "2. **Marketplaces**: Amazon India (SP-API ready) and Flipkart (Seller Hub sandbox ready).\n"
                    "3. **Social & Advertising**: Instagram Professional (Meta Graph API) and Facebook Catalog.\n"
                    "4. **Logistics & Feeds**: Shiprocket and Google Merchant Center feeds."
                ),
                suggested_actions=[
                    {"label": "Explore Channels", "action_url": "/#channels"},
                    {"label": "Start Free Workspace", "action_url": "/signup"},
                ],
                data_sources_used=["MarketPath Channel Capability Registry"],
            )

        # Consultation or Demo
        if "consult" in q_lower or "demo" in q_lower or "call" in q_lower or "talk" in q_lower:
            return PublicChatQueryResponse(
                answer=(
                    "You can schedule a comprehensive, no-obligation Free Consultation with our platform growth advisors. "
                    "We analyze your product categories, evaluate channel readiness, and formulate a customized omnichannel roadmap."
                ),
                suggested_actions=[
                    {"label": "Schedule Free Consultation", "action_url": "/free-consultation"},
                ],
                data_sources_used=["MarketPath Consultation Service"],
            )

        # Pricing or Plans
        if "pricing" in q_lower or "cost" in q_lower or "price" in q_lower or "plan" in q_lower:
            return PublicChatQueryResponse(
                answer=(
                    "MarketPath AI offers flexible, usage-based subscriptions designed for growing brands:\n\n"
                    "- **Starter**: 10 active SKUs, 1 channel connection.\n"
                    "- **Growth**: 100 active SKUs, 3 channel connections, full AI Studio.\n"
                    "- **Scale**: 500 active SKUs, 5 channel connections, priority sync.\n\n"
                    "Every merchant starts with a Free Consultation to receive personalized onboarding recommendations."
                ),
                suggested_actions=[
                    {"label": "Book Free Consultation", "action_url": "/free-consultation"},
                    {"label": "Start 14-Day Free Trial", "action_url": "/signup"},
                ],
                data_sources_used=["MarketPath Plan Architecture"],
            )

        # Registration / How to join
        if "register" in q_lower or "sign up" in q_lower or "signup" in q_lower or "create account" in q_lower or "join" in q_lower:
            return PublicChatQueryResponse(
                answer=(
                    "Creating a brand workspace is quick and simple. You can register with any standard business or personal email "
                    "(Gmail, Outlook, custom domain). No credit card is required to begin your 14-day free trial."
                ),
                suggested_actions=[
                    {"label": "Start Free Workspace", "action_url": "/signup"},
                    {"label": "Sign In to Existing Account", "action_url": "/login"},
                ],
                data_sources_used=["MarketPath Onboarding Guide"],
            )

        # Default platform overview
        return PublicChatQueryResponse(
            answer=(
                "MarketPath AI is the unified commerce and growth operating platform for emerging product brands. "
                "Our core promise: 'Describe your business and products once. Connect your selling channels. Approve your listings once. "
                "Manage your digital selling operations from one workspace.'\n\n"
                "I can explain supported channels, help you schedule a Free Consultation, or guide you through creating your brand workspace."
            ),
            suggested_actions=[
                {"label": "Start Free Workspace", "action_url": "/signup"},
                {"label": "Free Consultation", "action_url": "/free-consultation"},
                {"label": "How It Works", "action_url": "/about#how-it-works"},
            ],
            data_sources_used=["MarketPath Public Knowledge Base"],
        )

    @staticmethod
    async def answer_public_query(
        req: PublicChatQueryRequest,
    ) -> PublicChatQueryResponse:
        """Answers public queries with zero access to private tenant data."""
        # Always run deterministic checks first for private terms and core FAQs
        det_response = SupportBotService._deterministic_public_answer(req.message)
        if det_response.data_sources_used == ["Public Assistant Security Boundary"]:
            # Strictly return the boundary message if private keywords were triggered
            return det_response

        if not is_gemini_configured():
            return det_response

        system_instruction = """You are the MarketPath AI Public Assistant.
MarketPath AI is the unified commerce and growth operating platform for Indian D2C product brands.
Core Promise: "Describe your business and products once. Connect your selling channels. Approve your listings once. Manage your digital selling operations from one workspace."
10-Step Loop: Talk -> Understand -> Extract -> Structure -> Prepare -> Validate -> Approve -> Publish -> Synchronise -> Manage.

SECURITY BOUNDARY:
- You DO NOT have access to any customer accounts, orders, products, inventory, revenue, or personal data.
- If asked about an order, stock, product inventory, or private account data, refuse and state: "Order, product, and account information is available in your secure workspace after you sign in."
- Never invent private data or mock account details.
- Provide clear links to /login, /signup, or /free-consultation.
Output structured JSON matching PublicChatQueryResponse with keys: answer (string), suggested_actions (list of {label: string, action_url: string}), data_sources_used (list of string)."""

        prompt = f"""Conversation history:
{req.history}

Visitor query:
{req.message}"""

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            resp = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt + "\n\nReturn strictly valid JSON with keys: answer (string), suggested_actions (list of {label: string, action_url: string}), data_sources_used (list of string).",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            raw = json.loads(resp.text or "{}")
            return PublicChatQueryResponse.model_validate(raw)
        except Exception as e:
            logger.warning(f"Public chat Gemini query failed ({str(e)}). Falling back to deterministic public answer.")
            return det_response

