"""Demo Master Catalogue Fixture Seeder for Aura Terra Living.

Seeds deterministic, idempotent master catalogue records with variants, media,
dimensions, packaging specs, and inventory exclusively for DEMO_ORG_ID.
Ensures new real organizations start strictly with 0 records.
"""

import uuid
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.catalogue import Product, ProductVariant, ProductMedia

logger = logging.getLogger(__name__)


async def seed_demo_catalogue_if_empty(db: AsyncSession, demo_org_id: uuid.UUID) -> int:
    """Seeds sample master catalogue products for demo organization if empty."""
    existing_res = await db.execute(
        select(Product.id).where(Product.organization_id == demo_org_id).limit(1)
    )
    if existing_res.scalar_one_or_none():
        return 0  # Already seeded

    fixtures = [
        {
            "sku": "ATL-VASE-01",
            "title": "Artisanal Terracotta Vase",
            "category": "Home & Living / Decor",
            "status": "active",
            "base_price": 1499.00,
            "compare_at_price": 1999.00,
            "cost_price": 450.00,
            "currency": "INR",
            "stock_quantity": 45,
            "materials": ["Natural Terracotta Clay", "Organic Mineral Glaze"],
            "tags": ["Terracotta", "Handmade", "Vase", "Minimalist"],
            "dimensions": {"length": 18.0, "width": 18.0, "height": 28.0, "unit": "cm"},
            "weight": 1.20,
            "short_description": "Hand-turned terracotta vase with natural mineral wash finish.",
            "long_description": "Patiently hand-thrown by master potters in western India using regionally sourced riverbed clay. Each vase showcases unique earthy striations, bringing organic warmth to modern dining and living spaces.",
            "category_attributes": {
                "material_finish": "Raw Terracotta & Mineral Glaze",
                "room_placement": "Living, Dining, Entryway",
                "care_instructions": "Wipe with dry microfiber cloth. Avoid continuous water submersion.",
                "fragile": True,
            },
            "packaging_specs": {
                "box_length": 22.0,
                "box_width": 22.0,
                "box_height": 32.0,
                "box_unit": "cm",
                "dead_weight_grams": 1400,
                "volumetric_weight_grams": 3098,
                "packaging_material": "5-Ply Recycled Corrugated Box",
                "protective_packaging": "Biodegradable Honeycomb Paper Wrap",
            },
            "shipping_specs": {"fragile": True, "stackable": False},
            "moq": 1,
            "compliance_certificates": ["Lead-Free Glaze Certificate", "Plastic-Free Packaging"],
            "media_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=800&auto=format&fit=crop&q=80",
            "variants": [
                {
                    "sku": "ATL-VASE-01-OCHRE",
                    "title": "Artisanal Terracotta Vase - Matte Ochre",
                    "price": 1499.00,
                    "stock_quantity": 25,
                    "options": {"Finish": "Matte Ochre"},
                },
                {
                    "sku": "ATL-VASE-01-RAW",
                    "title": "Artisanal Terracotta Vase - Raw Earth",
                    "price": 1399.00,
                    "stock_quantity": 20,
                    "options": {"Finish": "Raw Earth"},
                },
            ],
        },
        {
            "sku": "ATL-CUSH-01",
            "title": "Handwoven Linen Cushion Cover",
            "category": "Home & Living / Decor",
            "status": "active",
            "base_price": 899.00,
            "compare_at_price": 1299.00,
            "cost_price": 260.00,
            "currency": "INR",
            "stock_quantity": 60,
            "materials": ["100% Belgian Flax Linen", "Azo-Free Botanical Dyes"],
            "tags": ["Linen", "Handwoven", "Cushion", "Sustainable Decor"],
            "dimensions": {"length": 45.0, "width": 45.0, "height": 2.0, "unit": "cm"},
            "weight": 0.25,
            "short_description": "Pure linen cushion cover with hand-stitched borders and hidden zip closure.",
            "long_description": "Woven on traditional pit-looms by artisan collectives. Pre-washed for cloud-like softness, breathable comfort, and timeless vintage appeal.",
            "category_attributes": {
                "material_finish": "Soft Washed Linen",
                "room_placement": "Sofa, Bed, Reading Nook",
                "care_instructions": "Machine wash gentle in cold water with mild detergent. Line dry in shade.",
                "fragile": False,
            },
            "packaging_specs": {
                "box_length": 30.0,
                "box_width": 25.0,
                "box_height": 4.0,
                "box_unit": "cm",
                "dead_weight_grams": 300,
                "volumetric_weight_grams": 600,
                "packaging_material": "Plant-Based Compostable Mailer",
                "protective_packaging": "Recycled Tissue Wrap",
            },
            "shipping_specs": {"fragile": False, "stackable": True},
            "moq": 1,
            "compliance_certificates": ["OEKO-TEX Certified Linen", "Zero Azo Dyes"],
            "media_url": "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=800&auto=format&fit=crop&q=80",
            "variants": [
                {
                    "sku": "ATL-CUSH-01-INDIGO",
                    "title": "Handwoven Linen Cushion Cover - Natural Indigo",
                    "price": 899.00,
                    "stock_quantity": 30,
                    "options": {"Color": "Natural Indigo"},
                },
                {
                    "sku": "ATL-CUSH-01-SAGE",
                    "title": "Handwoven Linen Cushion Cover - Earth Sage",
                    "price": 899.00,
                    "stock_quantity": 30,
                    "options": {"Color": "Earth Sage"},
                },
            ],
        },
        {
            "sku": "ATL-CNDL-01",
            "title": "Scented Soy Wax Candle Jar",
            "category": "Home Fragrance & Living",
            "status": "active",
            "base_price": 749.00,
            "compare_at_price": 999.00,
            "cost_price": 210.00,
            "currency": "INR",
            "stock_quantity": 80,
            "materials": ["100% Natural Soy Wax", "Braided Cotton Wick", "Pure Essential Oils"],
            "tags": ["Soy Candle", "Aromatherapy", "Clean Burn", "Gift Set"],
            "dimensions": {"length": 8.0, "width": 8.0, "height": 10.0, "unit": "cm"},
            "weight": 0.40,
            "short_description": "Clean-burning scented soy candle in amber glass vessel with cork lid.",
            "long_description": "Hand-poured in small batches in Pune using sustainable plant wax and pure botanical extracts. 45 hours of soot-free, comforting ambient glow.",
            "category_attributes": {
                "material_finish": "Amber Glass & Raw Cork",
                "burn_time_hours": 45,
                "care_instructions": "Trim wick to 1/4 inch before each lighting. Keep away from flammable materials.",
                "fragile": True,
            },
            "packaging_specs": {
                "box_length": 11.0,
                "box_width": 11.0,
                "box_height": 13.0,
                "box_unit": "cm",
                "dead_weight_grams": 450,
                "volumetric_weight_grams": 315,
                "packaging_material": "Heavyweight Kraft Tube Box",
                "protective_packaging": "Corrugated Sleeve",
            },
            "shipping_specs": {"fragile": True, "stackable": True},
            "moq": 1,
            "compliance_certificates": ["100% Phthalate Free", "Cruelty-Free & Vegan"],
            "media_url": "https://images.unsplash.com/photo-1603006905003-be475563bc59?w=800&auto=format&fit=crop&q=80",
            "variants": [
                {
                    "sku": "ATL-CNDL-01-CEDAR",
                    "title": "Scented Soy Candle - Himalayan Cedar & Amber",
                    "price": 749.00,
                    "stock_quantity": 40,
                    "options": {"Fragrance": "Himalayan Cedar"},
                },
                {
                    "sku": "ATL-CNDL-01-JASMINE",
                    "title": "Scented Soy Candle - Madurai Jasmine & Vanilla",
                    "price": 749.00,
                    "stock_quantity": 40,
                    "options": {"Fragrance": "Madurai Jasmine"},
                },
            ],
        },
        {
            "sku": "ATL-KLHD-01",
            "title": "Ceramic Chai Kulhad Set",
            "category": "Kitchen & Dining",
            "status": "active",
            "base_price": 899.00,
            "compare_at_price": 1199.00,
            "cost_price": 280.00,
            "currency": "INR",
            "stock_quantity": 50,
            "materials": ["Stoneware Clay", "Food-Grade Lead-Free Matte Glaze"],
            "tags": ["Chai Cups", "Kulhad", "Ceramic Tableware", "Indian Tea Culture"],
            "dimensions": {"length": 18.0, "width": 18.0, "height": 10.0, "unit": "cm"},
            "weight": 0.85,
            "short_description": "Set of handcrafted stoneware chai kulhad cups with earthy ribbed texture.",
            "long_description": "Designed for daily tea rituals. Ergonomic ribbed grip inspired by traditional railway kulhads, refined with durable microwave-safe and dishwasher-safe high-fire stoneware.",
            "category_attributes": {
                "material_finish": "Unglazed Terracotta Rim & Matte Ochre Base",
                "capacity_ml": 180,
                "care_instructions": "Microwave and dishwasher safe. Lead and cadmium free.",
                "fragile": True,
            },
            "packaging_specs": {
                "box_length": 21.0,
                "box_width": 21.0,
                "box_height": 12.0,
                "box_unit": "cm",
                "dead_weight_grams": 950,
                "volumetric_weight_grams": 1058,
                "packaging_material": "Custom Molded Pulp Tray & Corrugated Outer",
                "protective_packaging": "Molded Paper Pulp Separators",
            },
            "shipping_specs": {"fragile": True, "stackable": True},
            "moq": 1,
            "compliance_certificates": ["Food Safety Tested (Lead/Cadmium Free)", "Drop-Test Certified Packaging"],
            "media_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800&auto=format&fit=crop&q=80",
            "variants": [
                {
                    "sku": "ATL-KLHD-01-4PC",
                    "title": "Ceramic Chai Kulhad - 4-Piece Set",
                    "price": 899.00,
                    "stock_quantity": 35,
                    "options": {"Pack Size": "4 Pieces"},
                },
                {
                    "sku": "ATL-KLHD-01-6PC",
                    "title": "Ceramic Chai Kulhad - 6-Piece Set",
                    "price": 1299.00,
                    "stock_quantity": 15,
                    "options": {"Pack Size": "6 Pieces"},
                },
            ],
        },
    ]

    count = 0
    for f in fixtures:
        prod = Product(
            organization_id=demo_org_id,
            sku=f["sku"],
            title=f["title"],
            category=f["category"],
            status=f["status"],
            base_price=f["base_price"],
            compare_at_price=f["compare_at_price"],
            cost_price=f["cost_price"],
            currency=f["currency"],
            stock_quantity=f["stock_quantity"],
            materials=f["materials"],
            tags=f["tags"],
            dimensions=f["dimensions"],
            weight=f["weight"],
            short_description=f["short_description"],
            long_description=f["long_description"],
            category_attributes=f["category_attributes"],
            packaging_specs=f["packaging_specs"],
            shipping_specs=f["shipping_specs"],
            moq=f["moq"],
            compliance_certificates=f["compliance_certificates"],
        )
        db.add(prod)
        await db.flush()

        # Add primary media
        media = ProductMedia(
            product_id=prod.id,
            cloudinary_public_id=f"demo_{f['sku'].lower().replace('-', '_')}",
            media_url=f["media_url"],
            media_type="image",
            alt_text=f["title"],
            display_order=0,
        )
        db.add(media)

        # Add variants
        for v in f["variants"]:
            variant = ProductVariant(
                product_id=prod.id,
                sku=v["sku"],
                title=v["title"],
                price=v["price"],
                stock_quantity=v["stock_quantity"],
                options=v["options"],
            )
            db.add(variant)

        count += 1

    await db.commit()
    logger.info(f"Seeded {count} demo products for Aura Terra Living.")
    return count
