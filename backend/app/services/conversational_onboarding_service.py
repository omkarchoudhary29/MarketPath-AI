"""Conversational Business Onboarding Engine.

Enables natural conversation (typed text or transcribed voice) for brand and product intake.
Extracts structured brand identity (15 dimensions) and master product specifications.
Engages in multi-turn conversational follow-ups for missing information without demanding
every field at the beginning, generates editable confirmation drafts, and commits approved
records directly into existing BrandProfile and Product catalogue tables.
"""

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.brand import BrandProfile, BrandVoiceSession
from backend.app.models.catalogue import Product, ProductVariant
from backend.app.services.gemini_service import is_gemini_configured

logger = logging.getLogger(__name__)


class ExtractedBrandData(BaseModel):
    brand_name: Optional[str] = None
    tagline: Optional[str] = None
    founder_name: Optional[str] = None
    category: Optional[str] = None
    story: Optional[str] = None
    mission: Optional[str] = None
    brand_values: List[str] = []
    tone_of_voice: Optional[str] = "Warm & Aesthetic"
    archetype: Optional[str] = "Creator & Explorer"
    target_audience: Optional[str] = None
    usps: List[str] = []
    website: Optional[str] = None
    location: Optional[str] = None
    selling_channels: List[str] = []
    price_tier: Optional[str] = "Mid-Premium"


class ExtractedProductData(BaseModel):
    title: Optional[str] = None
    name: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    materials: List[str] = []
    colours: List[str] = []
    sizes: List[str] = []
    sku: Optional[str] = None
    base_price: Optional[float] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    weight_grams: Optional[float] = None
    dimensions_cm: Optional[Dict[str, float]] = None
    packaging: Optional[str] = None
    benefits: List[str] = []
    certifications: List[str] = []

    def model_post_init(self, __context: Any) -> None:
        if not self.title:
            self.title = self.name or self.product_name
        if self.base_price is None and self.price is not None:
            self.base_price = self.price


class ConversationalTurnResponse(BaseModel):
    reply_message: str
    assistant_message: Optional[str] = None
    extracted_brand: ExtractedBrandData
    extracted_products: List[ExtractedProductData]
    missing_fields_to_ask: List[str]
    missing_fields: List[str] = []
    is_ready_for_confirmation: bool

    def model_post_init(self, __context: Any) -> None:
        if not self.assistant_message:
            self.assistant_message = self.reply_message
        if not self.missing_fields:
            self.missing_fields = self.missing_fields_to_ask
        for p in self.extracted_products:
            if not p.title:
                p.title = p.name or p.product_name or "Handcrafted Artisanal Product"
        if not self.missing_fields:
            self.missing_fields = self.missing_fields_to_ask


class ConversationalOnboardingService:
    """Natural conversational intelligence for seller onboarding."""

    @staticmethod
    def _fallback_extract(user_message: str, history: List[Dict[str, str]]) -> ConversationalTurnResponse:
        """Deterministic NLP rule-based extractor when Gemini API is unconfigured."""
        full_text = " ".join([h.get("content", "") for h in history] + [user_message])
        
        # Extract Brand Name
        brand_match = re.search(r"(?:brand name is|brand is|called|named)\s+([A-Z][a-zA-Z0-9\s]+?)(?:\.|\,|$|\sand)", full_text, re.IGNORECASE)
        brand_name = brand_match.group(1).strip() if brand_match else None

        # Category
        cat = "Home & Gifting"
        if re.search(r"bamboo|wood|handicraft|gift|box|decor", full_text, re.IGNORECASE):
            cat = "Home & Living"
        elif re.search(r"apparel|clothing|dress|shirt", full_text, re.IGNORECASE):
            cat = "Apparel & Fashion"
        elif re.search(r"tea|coffee|food|gourmet|spice", full_text, re.IGNORECASE):
            cat = "Gourmet Food & Beverages"

        # Channels mentioned
        channels = []
        if re.search(r"amazon", full_text, re.IGNORECASE): channels.append("amazon")
        if re.search(r"flipkart", full_text, re.IGNORECASE): channels.append("flipkart")
        if re.search(r"shopify", full_text, re.IGNORECASE): channels.append("shopify")
        if re.search(r"instagram", full_text, re.IGNORECASE): channels.append("instagram")

        # Materials
        materials = []
        for mat in ["Bamboo", "Terracotta", "Cotton", "Brass", "Linen", "Clay", "Wood", "Glass", "Ceramic"]:
            if re.search(rf"\b{mat}\b", full_text, re.IGNORECASE):
                materials.append(mat)

        # Colours
        colours = []
        for col in ["Natural", "Brown", "Green", "White", "Black", "Terracotta", "Indigo", "Teal"]:
            if re.search(rf"\b{col}\b", full_text, re.IGNORECASE):
                colours.append(col)

        # Extract Prices
        base_price = 999.0
        mrp = 1299.0
        price_match = re.search(r"(?:priced at|selling at|price is|price:|₹|rs\.?)\s*(\d{2,6}(?:\.\d{1,2})?)", full_text, re.IGNORECASE)
        if price_match:
            try:
                base_price = float(price_match.group(1))
            except ValueError:
                pass

        mrp_match = re.search(r"(?:mrp|compare at)\s*[:₹\s]*(\d{2,6}(?:\.\d{1,2})?)", full_text, re.IGNORECASE)
        if mrp_match:
            try:
                mrp = float(mrp_match.group(1))
            except ValueError:
                pass
        else:
            mrp = round(base_price * 1.3, 2)

        # Missing field checks
        missing = []
        if not brand_name:
            missing.append("brand_name")
        if len(colours) == 0 and re.search(r"two colours|different colours|colours", full_text, re.IGNORECASE):
            missing.append("colours")
        if "amazon" in channels and not re.search(r"weight|\bkg\b|\bgm\b|\bgrams\b", full_text, re.IGNORECASE):
            missing.append("package_weight")

        # Conversational reply
        if "colours" in missing:
            reply = f"That sounds wonderful! You mentioned having different colours. What specific colour finishes do you offer for your {materials[0] if materials else 'products'}?"
        elif "package_weight" in missing:
            reply = f"Great! Since you plan to sell on Amazon, Amazon India requires the package shipping weight for Easy Ship delivery. What is the approximate packed weight?"
        elif brand_name:
            reply = f"I've noted your brand {brand_name} and your {materials[0] if materials else 'handcrafted'} products! I've prepared your draft Brand Profile below. Take a quick look and tell me if you'd like to adjust anything, or click Confirm to save them to your workspace."
        else:
            reply = "Hello! Welcome to MarketPath AI. I'm here to help set up your brand profile and product catalogue. Could you tell me your brand name and what kind of products you make?"

        brand_data = ExtractedBrandData(
            brand_name=brand_name or "",
            category=cat,
            story=f"{brand_name} manufactures authentic {cat.lower()}." if brand_name else "",
            tone_of_voice="Warm & Aesthetic",
            target_audience="Conscious consumers seeking authentic handcrafted products." if brand_name else "",
            selling_channels=channels or ["shopify", "amazon"],
            usps=["100% Handcrafted", "Made in India"] if brand_name else [],
        )

        prod_data_list: List[ExtractedProductData] = []
        has_prod_mention = bool(materials or re.search(r"product|selling|price|cup|vase|oil|candle|shirt|kurta|decor|mrp|kulhad|bottle", full_text, re.IGNORECASE))
        if has_prod_mention:
            prod_title = None
            title_match = re.search(r"(?:hero product is|flagship product is|product is|flagship is|craft|make|handcraft)\s+(?:a\s+|an\s+)?([A-Za-z0-9\s]+?)(?:priced|weighing|at ₹|at rs|in |\.\s|\,|$)", full_text, re.IGNORECASE)
            if title_match:
                candidate = title_match.group(1).strip()
                if len(candidate) > 3 and not re.search(r"^(brand|kitchenware|Pune|sustainable)$", candidate, re.IGNORECASE):
                    prod_title = candidate
            if not prod_title:
                prod_title = f"Handcrafted {' '.join(materials)} Product" if materials else f"{brand_name or 'Artisanal'} Product"

            prod_data_list.append(
                ExtractedProductData(
                    title=prod_title,
                    category=cat,
                    description="Patiently handcrafted with sustainable materials for thoughtful living and gifting.",
                    materials=materials or ["Natural Materials"],
                    colours=colours or ["Natural"],
                    sku=f"SKU-{(brand_name or 'MP')[:3].upper()}-01",
                    base_price=base_price,
                    mrp=mrp,
                    weight_grams=450.0,
                    dimensions_cm={"length": 20.0, "width": 15.0, "height": 8.0},
                )
            )

        return ConversationalTurnResponse(
            reply_message=reply,
            extracted_brand=brand_data,
            extracted_products=prod_data_list,
            missing_fields_to_ask=missing,
            is_ready_for_confirmation=bool(brand_name and len(missing) == 0),
        )

    @staticmethod
    async def process_turn(
        user_message: str,
        conversation_history: List[Dict[str, str]],
        existing_brand: Optional[BrandProfile] = None,
        audio_bytes: Optional[bytes] = None,
        audio_mime_type: str = "audio/webm",
    ) -> ConversationalTurnResponse:
        """Processes conversational input from the seller and extracts structured business data."""
        # If audio provided, transcribe first via Gemini Multimodal STT
        if audio_bytes and len(audio_bytes) > 60:
            from backend.app.services.gemini_service import transcribe_speech
            trans_res = await transcribe_speech(audio_bytes=audio_bytes, mime_type=audio_mime_type)
            transcript = trans_res.get("transcript", "").strip()
            if transcript:
                user_message = transcript
            else:
                return ConversationalTurnResponse(
                    reply_message="I didn't catch any speech in the audio. Please tap the microphone and speak again, or type your brand details below.",
                    extracted_brand=ExtractedBrandData(brand_name=existing_brand.brand_name if existing_brand else "", category="General"),
                    extracted_products=[],
                    missing_fields_to_ask=["brand_name", "products"],
                    is_ready_for_confirmation=False,
                )

        raw_text = (user_message or "").strip()
        cleaned = re.sub(r"[^\w\s]", "", raw_text).lower()
        greetings = {
            "hello", "hi", "hey", "namaste", "good morning", "good afternoon",
            "good evening", "hi there", "hello there", "start", "test", "marketpath",
        }
        if cleaned in greetings or len(cleaned) < 4:
            return ConversationalTurnResponse(
                reply_message="Hello! Welcome to MarketPath AI. I'm here to help you set up your brand and master product catalogue. What is your brand name, and what kind of products do you create?",
                extracted_brand=ExtractedBrandData(
                    brand_name=existing_brand.brand_name if existing_brand and existing_brand.brand_name else "",
                    category="General",
                    story=existing_brand.story if existing_brand else "",
                    tone_of_voice=existing_brand.tone_of_voice if existing_brand else "Warm & Aesthetic",
                    target_audience=existing_brand.target_audience_summary if existing_brand else "",
                ),
                extracted_products=[],
                missing_fields_to_ask=["brand_name", "category", "products", "materials"],
                is_ready_for_confirmation=False,
            )

        if not is_gemini_configured():
            return ConversationalOnboardingService._fallback_extract(user_message, conversation_history)

        system_instruction = """You are MarketPath AI, an empathetic and highly structured business assistant for Indian D2C product makers and manufacturers.
Your goal is to help a product maker onboard their brand and products through natural, friendly conversation.
CRITICAL RULES:
1. Do NOT interrogate or overwhelm the seller with 20 questions at once.
2. Extract as much structured brand info and product specs as possible from their words.
3. If they mentioned something ambiguous (e.g. 'I have two colours' but didn't name them), ask a natural, friendly follow-up question.
4. If they plan to sell on Amazon or Flipkart and a crucial requirement is missing (e.g. package weight or MRP), politely ask for it.
5. If the seller has NOT mentioned a specific product yet, leave extracted_products as an empty list []. Do NOT invent a fake product.
6. Return structured JSON matching the ConversationalTurnResponse schema.
7. Tone: Warm, helpful, professional, encouraging, acknowledging their craft."""

        # Format history
        history_text = "\n".join([f"{h.get('role', 'user')}: {h.get('content', '')}" for h in conversation_history])
        prompt = f"""Conversation history so far:
{history_text}

New seller message:
{user_message}

Please extract structured Brand and Product details (leave extracted_products empty if no product was described), identify if any crucial missing information should be asked in a single friendly follow-up, and generate your conversational response."""

        for model_name in [settings.GEMINI_MODEL, "gemini-3.5-flash-lite", "gemini-3.8-flash"]:
            try:
                client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"api_version": "v1alpha"})
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                    + "\n\nReturn strictly valid JSON with keys: reply_message (string), extracted_brand (object), extracted_products (list of objects with fields: title, category, description, materials, colours, base_price, mrp, weight_grams), missing_fields_to_ask (list of string), is_ready_for_confirmation (boolean).",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.3,
                    ),
                )
                raw = json.loads(resp.text or "{}")
                turn = ConversationalTurnResponse.model_validate(raw)
                for p in turn.extracted_products:
                    if not p.title:
                        p.title = getattr(p, "name", None) or getattr(p, "product_name", None) or "Handcrafted Artisanal Product"
                return turn
            except Exception as e:
                logger.warning(f"Conversational turn with {model_name} failed: {e}")

        return ConversationalOnboardingService._fallback_extract(user_message, conversation_history)

    @staticmethod
    async def confirm_and_save(
        db: AsyncSession,
        organization_id: uuid.UUID,
        brand_data: ExtractedBrandData,
        products_data: List[ExtractedProductData],
    ) -> Dict[str, Any]:
        """Saves approved conversational data directly into BrandProfile and Master Product Catalogue."""
        # 1. Update or create BrandProfile
        b_stmt = select(BrandProfile).where(BrandProfile.organization_id == organization_id)
        b_res = await db.execute(b_stmt)
        brand = b_res.scalar_one_or_none()

        if not brand:
            brand = BrandProfile(organization_id=organization_id)
            db.add(brand)

        if brand_data.brand_name:
            brand.brand_name = brand_data.brand_name
        if brand_data.tagline:
            brand.tagline = brand_data.tagline
        if brand_data.story:
            brand.story = brand_data.story
        if brand_data.mission:
            brand.mission = brand_data.mission
        if brand_data.brand_values:
            brand.brand_values = brand_data.brand_values
        if brand_data.tone_of_voice:
            brand.tone_of_voice = brand_data.tone_of_voice
        if brand_data.archetype:
            brand.archetype = brand_data.archetype
        if brand_data.target_audience:
            brand.target_audience = brand_data.target_audience
            brand.target_audience_summary = brand_data.target_audience
        if brand_data.usps:
            brand.key_usps = brand_data.usps
        if brand_data.price_tier:
            brand.pricing_strategy = brand_data.price_tier

        # Retain extra business metadata in customer_demographics dictionary
        demographics = dict(brand.customer_demographics or {})
        if brand_data.founder_name:
            demographics["founder_name"] = brand_data.founder_name
        if brand_data.website:
            demographics["website"] = brand_data.website
        if brand_data.location:
            demographics["location"] = brand_data.location
        if brand_data.category:
            demographics["category"] = brand_data.category
        if brand_data.selling_channels:
            demographics["selling_channels"] = brand_data.selling_channels
        brand.customer_demographics = demographics

        await db.flush()

        # 2. Save products into master catalogue
        saved_products = []
        for p_data in products_data:
            if not p_data.title:
                continue

            sku = p_data.sku or f"SKU-{uuid.uuid4().hex[:6].upper()}"

            # Check if SKU already exists in this org
            existing_p = await db.execute(
                select(Product).where(Product.organization_id == organization_id, Product.sku == sku)
            )
            prod = existing_p.scalar_one_or_none()
            if not prod:
                prod = Product(
                    organization_id=organization_id,
                    brand_profile_id=brand.id,
                    sku=sku,
                    title=p_data.title,
                    category=p_data.category or (brand_data.category or "General"),
                    base_price=p_data.base_price or 999.0,
                    compare_at_price=p_data.mrp or ((p_data.base_price or 999.0) * 1.3),
                    currency="INR",
                    short_description=p_data.description or f"Authentic handcrafted {p_data.title}.",
                    long_description=p_data.description or f"Premium handcrafted {p_data.title} made with sustainable materials.",
                    materials=p_data.materials or [],
                    weight=p_data.weight_grams or 500.0,
                    dimensions=p_data.dimensions_cm or {"length": 15, "width": 10, "height": 8},
                    stock_quantity=50,
                    status="active",
                    packaging_specs={"packaging_type": p_data.packaging or "Recycled Kraft Carton"},
                    category_attributes={
                        "colours": p_data.colours,
                        "sizes": p_data.sizes,
                        "benefits": p_data.benefits,
                        "country_of_origin": "India",
                    },
                )
                db.add(prod)
                await db.flush()

                # If variants (colours or sizes)
                if p_data.colours and len(p_data.colours) > 1:
                    for col in p_data.colours:
                        v = ProductVariant(
                            product_id=prod.id,
                            sku=f"{prod.sku}-{col.upper().replace(' ', '_')}",
                            title=f"{prod.title} - {col}",
                            price=prod.base_price,
                            stock_quantity=25,
                            options={"Color": col},
                        )
                        db.add(v)

            saved_products.append(prod.sku)

        await db.commit()
        return {
            "success": True,
            "status": "success",
            "brand_id": str(brand.id),
            "brand_name": brand.brand_name,
            "products_saved": len(saved_products),
            "products_created": len(saved_products),
            "skus": saved_products,
        }
