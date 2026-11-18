"""Product Intake and Information Extraction Service.

Processes unstructured text or spoken audio to extract master product specifications,
dimensions, materials, pricing, variants, and marketplace compliance requirements.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.services.gemini_service import is_gemini_configured

logger = logging.getLogger(__name__)


class ExtractedProductDraft(BaseModel):
    title: str = "Handcrafted Artisanal Product"
    category: str = "Home & Living / Decor"
    short_description: str = ""
    long_description: str = ""
    base_price: float = 999.0
    compare_at_price: Optional[float] = 1299.0
    cost_price: Optional[float] = None
    materials: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    weight_kg: Optional[float] = 0.5
    dimensions_cm: Dict[str, float] = Field(default_factory=lambda: {"length": 15.0, "width": 12.0, "height": 10.0})
    packaging_specs: Dict[str, Any] = Field(default_factory=dict)
    category_attributes: Dict[str, Any] = Field(default_factory=dict)
    suggested_variants: List[Dict[str, Any]] = Field(default_factory=list)
    missing_marketplace_fields: List[str] = Field(default_factory=list)
    raw_transcript: Optional[str] = None
    confidence_score: float = 0.90


class ProductIntakeService:
    """Extracts master product records from unstructured audio or text."""

    @staticmethod
    def _deterministic_extract(text: str, category_hint: Optional[str] = None) -> ExtractedProductDraft:
        """Rule-based extractor for reliable parsing without external AI API dependencies."""
        raw_text = text.strip()
        lower = raw_text.lower()

        # 1. Determine Title & Category
        cat = category_hint or "Home & Living / Decor"
        if any(w in lower for w in ["shirt", "dress", "kurta", "linen", "cotton", "apparel", "fabric", "wear"]):
            cat = "Apparel & Accessories"
        elif any(w in lower for w in ["tea", "coffee", "spice", "honey", "snack", "gourmet", "food"]):
            cat = "Food & Beverages"
        elif any(w in lower for w in ["soap", "oil", "serum", "candle", "fragrance", "skin", "cream"]):
            cat = "Beauty & Wellness"

        # Guess title
        title = "Handcrafted Artisanal Product"
        title_patterns = [
            r"(?:making|product is|called|named|hero product is|crafting|selling)\s+([A-Z0-9][a-zA-Z0-9\s\-]+?)(?:\s+priced|\s+costs|\s+with|\s+at|\.|\,|$)",
            r"^([A-Z][a-zA-Z0-9\s\-]{3,40})",
        ]
        for pat in title_patterns:
            m = re.search(pat, raw_text)
            if m and len(m.group(1).strip()) > 3:
                title = m.group(1).strip()
                break

        # 2. Extract Prices
        base_price = 999.0
        compare_at_price = 1299.0
        cost_price = None

        selling_match = re.search(r"(?:selling price|priced at|selling at|price is|price:|price\s+|₹|rs\.?)\s*[:₹\s]*(\d{2,6}(?:\.\d{1,2})?)", raw_text, re.IGNORECASE)
        if not selling_match:
            selling_match = re.search(r"(\d{2,6}(?:\.\d{1,2})?)\s*(?:rupees|rs|inr)", raw_text, re.IGNORECASE)
        if selling_match:
            try:
                base_price = float(selling_match.group(1))
            except ValueError:
                pass

        mrp_match = re.search(r"(?:mrp|compare at|retail price|mrp is|mrp of)\s*[:₹\s]*(\d{2,6}(?:\.\d{1,2})?)", raw_text, re.IGNORECASE)
        if mrp_match:
            try:
                compare_at_price = float(mrp_match.group(1))
            except ValueError:
                pass
        else:
            compare_at_price = round(base_price * 1.3, 2)

        cost_match = re.search(r"(?:cost price|cost is|making cost|production cost)\s*[:₹\s]*(\d{2,6}(?:\.\d{1,2})?)", raw_text, re.IGNORECASE)
        if cost_match:
            try:
                cost_price = float(cost_match.group(1))
            except ValueError:
                pass

        # 3. Extract Materials
        materials_library = [
            "Terracotta", "Ceramic", "Clay", "Sheesham Wood", "Teak Wood", "Bamboo",
            "Brass", "Copper", "Linen", "Organic Cotton", "Soy Wax", "Jute", "Glass",
        ]
        detected_materials = [mat for mat in materials_library if re.search(rf"\b{mat}\b", raw_text, re.IGNORECASE)]
        if not detected_materials:
            detected_materials = ["Natural Sustainable Materials"]

        # 4. Extract Dimensions
        dim_match = re.search(r"(\d+(?:\.\d+)?)\s*[xX*]\s*(\d+(?:\.\d+)?)\s*(?:[xX*]\s*(\d+(?:\.\d+)?))?\s*(cm|mm|inches|in)?", raw_text)
        if dim_match:
            l = float(dim_match.group(1))
            w = float(dim_match.group(2))
            h = float(dim_match.group(3)) if dim_match.group(3) else 5.0
            dimensions = {"length": l, "width": w, "height": h}
        else:
            len_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:cm|mm)?\s*(?:length|long)", raw_text, re.IGNORECASE) or re.search(r"(?:length|long)\s*(?:is|:)?\s*(\d+(?:\.\d+)?)", raw_text, re.IGNORECASE)
            wid_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:cm|mm)?\s*(?:width|wide)", raw_text, re.IGNORECASE) or re.search(r"(?:width|wide)\s*(?:is|:)?\s*(\d+(?:\.\d+)?)", raw_text, re.IGNORECASE)
            hgt_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:cm|mm)?\s*(?:height|high)", raw_text, re.IGNORECASE) or re.search(r"(?:height|high)\s*(?:is|:)?\s*(\d+(?:\.\d+)?)", raw_text, re.IGNORECASE)
            if len_m and wid_m:
                dimensions = {
                    "length": float(len_m.group(1)),
                    "width": float(wid_m.group(1)),
                    "height": float(hgt_m.group(1)) if hgt_m else 5.0,
                }
            else:
                dimensions = {"length": 15.0, "width": 12.0, "height": 10.0}

        # 5. Extract Weight
        weight_kg = 0.45
        weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:g|gm|grams|kg|kilo)", lower)
        if weight_match:
            val = float(weight_match.group(1))
            weight_kg = val / 1000.0 if val > 20 else val

        # 6. Detect Variants (Colors / Sizes)
        variants = []
        colours = []
        for col in ["Natural", "Brown", "Ochre", "Terracotta", "Indigo", "Sage Green", "Matte Black", "White", "Dark Walnut"]:
            if re.search(rf"\b{col}\b", raw_text, re.IGNORECASE):
                colours.append(col)

        sizes = []
        for sz in ["Small", "Medium", "Large", "Set of 2", "Set of 4", "Set of 6"]:
            if re.search(rf"\b{sz}\b", raw_text, re.IGNORECASE):
                sizes.append(sz)

        if colours and len(colours) > 1:
            for c in colours:
                variants.append({
                    "title": f"{title} - {c}",
                    "option_key": "Color",
                    "option_value": c,
                    "price": base_price,
                    "stock_quantity": 20,
                })
        elif sizes and len(sizes) > 1:
            for s in sizes:
                variants.append({
                    "title": f"{title} - {s}",
                    "option_key": "Size",
                    "option_value": s,
                    "price": base_price,
                    "stock_quantity": 15,
                })
        else:
            variants.append({
                "title": "Standard",
                "option_key": "Finish",
                "option_value": colours[0] if colours else "Natural",
                "price": base_price,
                "stock_quantity": 30,
            })

        # 7. Missing marketplace requirements check
        missing = []
        if not re.search(r"weight|\bg\b|\bgm\b|\bgrams\b|\bkg\b", lower):
            missing.append("Package Shipping Weight (Required for Amazon Easy Ship & Delhivery)")
        if not mrp_match:
            missing.append("Maximum Retail Price / MRP (Mandatory for Indian Legal Metrology)")
        if not re.search(r"hsn", lower):
            missing.append("HSN Tax Code (Required for GST Invoicing on Amazon & Flipkart)")
        if not re.search(r"box|carton|packaging|packed in", lower):
            missing.append("Protective Packaging Specification (Required for fragile transit claims)")

        # Packaging specs
        box_l = round(dimensions["length"] + 3.0, 1)
        box_w = round(dimensions["width"] + 3.0, 1)
        box_h = round(dimensions["height"] + 3.0, 1)
        dead_weight_g = round(weight_kg * 1000)
        volumetric_g = round(((box_l * box_w * box_h) / 5000) * 1000)

        packaging_specs = {
            "box_length": box_l,
            "box_width": box_w,
            "box_height": box_h,
            "box_unit": "cm",
            "dead_weight_grams": dead_weight_g,
            "volumetric_weight_grams": volumetric_g,
            "packaging_material": "Recycled Corrugated Box",
            "protective_packaging": "Honeycomb Paper Cushioning",
        }

        short_desc = f"Handcrafted {title} made with authentic {', '.join(detected_materials[:2])}."
        long_desc = (
            f"Each {title} is thoughtfully shaped by skilled artisans using sustainable {', '.join(detected_materials)}. "
            f"Designed for modern mindful homes with enduring natural charm. Dimensions: {dimensions['length']}x{dimensions['width']}x{dimensions['height']} cm."
        )

        return ExtractedProductDraft(
            title=title,
            category=cat,
            short_description=short_desc,
            long_description=long_desc,
            base_price=base_price,
            compare_at_price=compare_at_price,
            cost_price=cost_price,
            materials=detected_materials,
            tags=["Artisanal", cat.split("/")[0].strip()] + detected_materials[:2],
            weight_kg=weight_kg,
            dimensions_cm=dimensions,
            packaging_specs=packaging_specs,
            category_attributes={
                "material_finish": colours[0] if colours else "Natural Matte",
                "care_instructions": "Wipe with clean dry cloth. Keep away from harsh abrasives.",
                "fragile": True if any(m in detected_materials for m in ["Ceramic", "Terracotta", "Clay", "Glass"]) else False,
            },
            suggested_variants=variants,
            missing_marketplace_fields=missing,
            raw_transcript=raw_text,
            confidence_score=0.92,
        )

    @classmethod
    async def extract_from_text(cls, text: str, category_hint: Optional[str] = None) -> ExtractedProductDraft:
        """Extracts structured product data from text using Gemini if available, or fallback."""
        if not text or len(text.strip()) < 4:
            return ExtractedProductDraft(
                title="",
                category=category_hint or "Home & Living / Decor",
                raw_transcript=text,
                confidence_score=0.0,
                base_price=0.0,
                compare_at_price=0.0,
                weight_kg=0.0,
                dimensions_cm={"length": 0.0, "width": 0.0, "height": 0.0},
                missing_marketplace_fields=["title", "materials", "base_price", "dimensions", "weight"],
            )

        from backend.app.services.gemini_service import extract_product_specifications
        try:
            raw = await extract_product_specifications(text, category_hint)
            raw["raw_transcript"] = text
            if not raw.get("confidence_score"):
                raw["confidence_score"] = 0.95
            return ExtractedProductDraft.model_validate(raw)
        except Exception as e:
            logger.warning(f"Product extraction failed: {e}, using deterministic parser.")
            draft = cls._deterministic_extract(text, category_hint)
            draft.raw_transcript = text
            return draft

    @classmethod
    async def extract_from_audio(
        cls,
        audio_bytes: bytes,
        mime_type: str = "audio/webm",
        category_hint: Optional[str] = None,
    ) -> ExtractedProductDraft:
        """Transcribes and extracts structured product data directly from user voice audio."""
        from backend.app.services.gemini_service import transcribe_speech

        # Step A: Verbatim Speech-to-Text
        transcription = await transcribe_speech(audio_bytes=audio_bytes, mime_type=mime_type)
        transcript = transcription.get("transcript", "").strip()

        if not transcript:
            return ExtractedProductDraft(
                title="",
                category=category_hint or "Home & Living / Decor",
                raw_transcript="",
                confidence_score=0.0,
                base_price=0.0,
                compare_at_price=0.0,
                weight_kg=0.0,
                dimensions_cm={"length": 0.0, "width": 0.0, "height": 0.0},
                missing_marketplace_fields=["title", "materials", "base_price", "dimensions", "weight"],
            )

        # Step B: Structured Extraction from Verbatim Transcript
        return await cls.extract_from_text(transcript, category_hint)
