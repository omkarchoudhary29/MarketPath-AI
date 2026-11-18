"""Channel Mapping Engine.

Maps MarketPath master product catalogue entities and channel overrides
to platform-specific schemas (Shopify Admin GraphQL, Instagram Graph API).
Ensures the master product remains immutable and validates platform-specific rules.
"""

from typing import Any, Dict, List, Optional, Tuple
from backend.app.models.catalogue import Product, ProductChannelOverride


class ChannelMappingError(Exception):
    """Raised when channel mapping fails validation."""
    pass


class ChannelMapper:
    """Transforms master products into channel-compliant payloads."""

    @staticmethod
    def validate_for_shopify(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
    ) -> Tuple[bool, List[str], List[str]]:
        """Validates product for Shopify Admin API publishing.
        
        Returns:
            (is_valid, errors, warnings)
        """
        errors: List[str] = []
        warnings: List[str] = []

        title = (override.custom_title if override and override.custom_title else product.title) or ""
        if not title.strip():
            errors.append("Product title is required for Shopify.")
        elif len(title) > 255:
            errors.append(f"Product title exceeds Shopify 255 character limit ({len(title)} chars).")

        price = (override.custom_price if override and override.custom_price is not None else product.base_price) or 0.0
        try:
            if float(price) <= 0:
                errors.append("Base price must be greater than zero for Shopify.")
        except (ValueError, TypeError):
            errors.append("Base price must be a valid numeric value.")

        if not product.sku or not product.sku.strip():
            warnings.append("Master SKU is empty; Shopify inventory tracking will be limited.")

        if not product.category or not product.category.strip():
            warnings.append("Category is missing; Shopify will classify under default category.")

        description = (
            override.custom_description if override and override.custom_description
            else product.long_description or product.short_description or ""
        )
        if not description.strip():
            warnings.append("Product description is empty; listings with rich descriptions convert better.")

        if not product.media or len(product.media) == 0:
            warnings.append("No product images uploaded. Shopify listings without images may be rejected by sales channels.")

        if product.variants and len(product.variants) > 100:
            errors.append(f"Shopify allows a maximum of 100 variants per product (found {len(product.variants)}).")

        for idx, variant in enumerate(product.variants or []):
            try:
                if float(variant.price) <= 0:
                    errors.append(f"Variant #{idx + 1} ('{variant.title}') has invalid price <= 0.")
            except (ValueError, TypeError):
                errors.append(f"Variant #{idx + 1} has non-numeric price.")
            if not variant.sku:
                warnings.append(f"Variant #{idx + 1} ('{variant.title}') is missing SKU.")

        return len(errors) == 0, errors, warnings

    @staticmethod
    def map_to_shopify_graphql(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
        vendor_name: str = "MarketPath Seller",
    ) -> Dict[str, Any]:
        """Converts master product + override into Shopify Admin GraphQL productCreate payload."""
        title = (override.custom_title if override and override.custom_title else product.title) or ""
        raw_description = (
            override.custom_description if override and override.custom_description
            else product.long_description or product.short_description or ""
        )
        description_html = f"<p>{raw_description.replace('\n', '<br/>')}</p>" if raw_description else ""

        category = (
            override.category_mapping if override and override.category_mapping
            else product.category
        )
        tags = (
            override.custom_tags if override and override.custom_tags
            else product.tags or []
        )

        price = (
            override.custom_price if override and override.custom_price is not None
            else product.base_price
        )

        # Build variants
        shopify_variants: List[Dict[str, Any]] = []
        if product.variants and len(product.variants) > 0:
            for variant in product.variants:
                v_price = float(variant.price)
                v_dict: Dict[str, Any] = {
                    "price": f"{v_price:.2f}",
                    "sku": variant.sku or f"{product.sku}-{variant.title.upper().replace(' ', '_')}",
                    "inventoryQuantity": int(variant.stock_quantity or 0),
                }
                # If variant has options dict (e.g. {"Size": "L", "Color": "Blue"})
                if variant.options and isinstance(variant.options, dict):
                    v_dict["options"] = [str(val) for val in variant.options.values()]
                else:
                    v_dict["options"] = [variant.title]
                shopify_variants.append(v_dict)
        else:
            # Single default variant from master product
            shopify_variants.append({
                "price": f"{float(price):.2f}",
                "sku": product.sku,
                "inventoryQuantity": int(product.stock_quantity or 0),
                "options": ["Default Title"],
            })

        # Build media / images
        shopify_media: List[Dict[str, Any]] = []
        for media_item in sorted(product.media or [], key=lambda m: m.display_order):
            if media_item.media_url and media_item.media_url.startswith("http"):
                shopify_media.append({
                    "originalSource": media_item.media_url,
                    "alt": media_item.alt_text or title,
                    "mediaContentType": "IMAGE",
                })

        product_status = "ACTIVE" if product.status == "active" else "DRAFT"

        return {
            "input": {
                "title": title,
                "descriptionHtml": description_html,
                "vendor": vendor_name,
                "productType": category,
                "status": product_status,
                "tags": tags,
                "variants": shopify_variants,
            },
            "media": shopify_media,
        }

    @staticmethod
    def validate_for_instagram(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
    ) -> Tuple[bool, List[str], List[str]]:
        """Validates product for Instagram Graph API organic publishing.
        
        Returns:
            (is_valid, errors, warnings)
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Instagram organic post requires at least one image
        if not product.media or len(product.media) == 0:
            errors.append("Instagram organic post requires at least one media asset (image).")
        else:
            first_media = product.media[0]
            if not first_media.media_url.startswith("https://"):
                errors.append(f"Instagram requires a publicly accessible HTTPS image URL (got '{first_media.media_url[:30]}...').")

        # Caption validation
        raw_caption = (
            override.custom_description if override and override.custom_description
            else product.short_description or product.title or ""
        )
        if len(raw_caption) > 2200:
            errors.append(f"Instagram caption exceeds 2,200 character limit ({len(raw_caption)} chars).")

        tags = override.custom_tags if override and override.custom_tags else product.tags or []
        if len(tags) > 30:
            warnings.append(f"Instagram recommends maximum 30 hashtags (found {len(tags)}).")

        return len(errors) == 0, errors, warnings

    @staticmethod
    def map_to_instagram_post(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
        brand_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Converts master product + override into Instagram Media Container creation payload."""
        # Select first image
        image_url = ""
        if product.media and len(product.media) > 0:
            image_url = product.media[0].media_url

        # Build caption
        title = (override.custom_title if override and override.custom_title else product.title) or ""
        description = (
            override.custom_description if override and override.custom_description
            else product.short_description or product.long_description or ""
        )
        price_str = f"₹{product.base_price:.2f}" if product.currency == "INR" else f"{product.currency} {product.base_price:.2f}"

        tags = override.custom_tags if override and override.custom_tags else product.tags or []
        hashtags_formatted = " ".join([f"#{t.replace(' ', '').replace('-', '')}" for t in tags[:25] if t])

        brand_line = f"Brand: {brand_name}\n" if brand_name else ""
        caption_parts = [
            title,
            f"Price: {price_str}",
            "",
            description,
            "",
            brand_line,
            hashtags_formatted,
        ]
        caption = "\n".join([p for p in caption_parts if p.strip()]).strip()
        if len(caption) > 2200:
            caption = caption[:2197] + "..."

        return {
            "image_url": image_url,
            "caption": caption,
            "media_type": "IMAGE",
        }

    # ==========================================
    # WOOCOMMERCE MAPPING
    # ==========================================
    @staticmethod
    def validate_for_woocommerce(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
    ) -> Tuple[bool, List[str], List[str]]:
        """Validates product for WooCommerce REST API v3."""
        errors: List[str] = []
        warnings: List[str] = []

        title = (override.custom_title if override and override.custom_title else product.title) or ""
        if not title.strip():
            errors.append("Product name is required for WooCommerce.")

        price = (override.custom_price if override and override.custom_price is not None else product.base_price) or 0.0
        try:
            if float(price) <= 0:
                errors.append("Regular price must be greater than zero for WooCommerce.")
        except (ValueError, TypeError):
            errors.append("Price must be a valid numeric number.")

        if not product.sku or not product.sku.strip():
            warnings.append("SKU is empty; WooCommerce stock tracking per SKU will be disabled.")

        if not product.media or len(product.media) == 0:
            warnings.append("No product image provided for WooCommerce catalogue display.")

        return len(errors) == 0, errors, warnings

    @staticmethod
    def map_to_woocommerce(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
    ) -> Dict[str, Any]:
        """Maps master product to WooCommerce POST /wp-json/wc/v3/products payload."""
        title = (override.custom_title if override and override.custom_title else product.title) or ""
        description = (
            override.custom_description if override and override.custom_description
            else product.long_description or product.short_description or ""
        )
        short_description = product.short_description or ""
        price = (override.custom_price if override and override.custom_price is not None else product.base_price) or 0.0

        images = []
        for media_item in sorted(product.media or [], key=lambda m: m.display_order):
            if media_item.media_url and media_item.media_url.startswith("http"):
                images.append({"src": media_item.media_url, "alt": media_item.alt_text or title})

        dims = product.dimensions or {}
        dimensions_dict = {
            "length": str(dims.get("length", "")),
            "width": str(dims.get("width", "")),
            "height": str(dims.get("height", "")),
        }

        # Categories
        cat_name = (override.category_mapping if override and override.category_mapping else product.category) or "General"
        categories = [{"name": cat_name}]

        return {
            "name": title,
            "type": "simple" if not product.variants else "variable",
            "regular_price": f"{float(price):.2f}",
            "description": f"<p>{description.replace(chr(10), '<br/>')}</p>",
            "short_description": short_description,
            "sku": product.sku,
            "manage_stock": True,
            "stock_quantity": int(product.stock_quantity or 0),
            "dimensions": dimensions_dict,
            "weight": str(product.weight) if product.weight else "",
            "categories": categories,
            "images": images,
        }

    # ==========================================
    # AMAZON INDIA (SP-API) MAPPING & REQUIREMENTS
    # ==========================================
    @staticmethod
    def get_amazon_missing_fields(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
    ) -> List[Dict[str, Any]]:
        """Identifies missing mandatory fields required by Amazon SP-API."""
        missing = []

        # 1. Package weight
        packaging = product.packaging_specs or {}
        shipping = product.shipping_specs or {}
        pkg_weight = product.weight or shipping.get("shipping_weight_grams")
        if not pkg_weight:
            missing.append({
                "field": "package_weight",
                "label": "Package Shipping Weight",
                "type": "number",
                "description": "Amazon India requires item package weight in grams/kg for FBA and Easy Ship calculation.",
                "required": True,
            })

        # 2. Package dimensions
        dims = packaging.get("box_dimensions") or product.dimensions or {}
        if not (dims.get("length") and dims.get("width") and dims.get("height")):
            missing.append({
                "field": "package_dimensions",
                "label": "Package Carton Dimensions (L x W x H)",
                "type": "dimensions",
                "description": "Amazon requires length, width, and height in cm.",
                "required": True,
            })

        # 3. Country of origin
        cat_attrs = product.category_attributes or {}
        if not cat_attrs.get("country_of_origin"):
            missing.append({
                "field": "country_of_origin",
                "label": "Country of Origin",
                "type": "text",
                "default": "India",
                "description": "Mandatory Legal Metrology requirement under Indian e-commerce rules.",
                "required": True,
            })

        # 4. Bullet Points / Key Product Features
        bullet_points = cat_attrs.get("bullet_points") or []
        if not bullet_points and not (product.tags and len(product.tags) >= 2):
            missing.append({
                "field": "bullet_points",
                "label": "Key Product Bullet Points (At least 3)",
                "type": "list",
                "description": "Bullet points highlighting material, usage, and dimensions for Amazon detail page.",
                "required": True,
            })

        # 5. HSN Code
        if not cat_attrs.get("hsn_code"):
            missing.append({
                "field": "hsn_code",
                "label": "GST HSN Code",
                "type": "text",
                "description": "Harmonized System of Nomenclature code for GST compliance on Amazon India.",
                "required": True,
            })

        return missing

    @staticmethod
    def validate_for_amazon(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
    ) -> Tuple[bool, List[str], List[str]]:
        """Validates product for Amazon SP-API Listings Items submission."""
        errors: List[str] = []
        warnings: List[str] = []

        title = (override.custom_title if override and override.custom_title else product.title) or ""
        if not title.strip():
            errors.append("Item Name (Title) is mandatory for Amazon SP-API.")
        elif len(title) > 200:
            errors.append(f"Amazon item title exceeds 200 character limit ({len(title)} chars).")

        price = (override.custom_price if override and override.custom_price is not None else product.base_price) or 0.0
        try:
            if float(price) <= 0:
                errors.append("Standard Price must be greater than zero for Amazon.")
        except (ValueError, TypeError):
            errors.append("Standard Price must be a valid number.")

        if not product.sku:
            errors.append("Master Seller SKU is required for Amazon SP-API listing item key.")

        missing_fields = ChannelMapper.get_amazon_missing_fields(product, override)
        for mf in missing_fields:
            if mf.get("required"):
                errors.append(f"Amazon India missing field: {mf['label']}")

        if not product.media or len(product.media) == 0:
            errors.append("Amazon requires at least one high-resolution main image with pure white background (1000x1000px+).")

        return len(errors) == 0, errors, warnings

    @staticmethod
    def map_to_amazon_sp_api(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
        brand_name: str = "MarketPath Brand",
    ) -> Dict[str, Any]:
        """Converts master product into Amazon SP-API Listings Items attributes dictionary."""
        title = (override.custom_title if override and override.custom_title else product.title) or ""
        price = (override.custom_price if override and override.custom_price is not None else product.base_price) or 0.0
        description = (
            override.custom_description if override and override.custom_description
            else product.long_description or product.short_description or ""
        )

        cat_attrs = product.category_attributes or {}
        packaging = product.packaging_specs or {}
        dims = packaging.get("box_dimensions") or product.dimensions or {}

        # Bullets
        bullets = cat_attrs.get("bullet_points") or [
            f"Handcrafted {product.title} made from premium materials.",
            f"Dimensions: {dims.get('length', '')} x {dims.get('width', '')} x {dims.get('height', '')} cm.",
            "Designed and manufactured in India.",
        ]

        main_image = product.media[0].media_url if product.media and len(product.media) > 0 else ""

        return {
            "item_name": [{"value": title, "marketplace_id": "A21TJRUUN4KGV"}],
            "purchasable_offer": [{
                "marketplace_id": "A21TJRUUN4KGV",
                "currency": product.currency or "INR",
                "our_price": [{"schedule": [{"value_with_tax": float(price)}]}]
            }],
            "product_description": [{"value": description, "marketplace_id": "A21TJRUUN4KGV"}],
            "bullet_point": [{"value": b, "marketplace_id": "A21TJRUUN4KGV"} for b in bullets[:5]],
            "brand": [{"value": brand_name, "marketplace_id": "A21TJRUUN4KGV"}],
            "country_of_origin": [{"value": cat_attrs.get("country_of_origin", "India"), "marketplace_id": "A21TJRUUN4KGV"}],
            "main_product_image_locator": [{"media_location": main_image, "marketplace_id": "A21TJRUUN4KGV"}] if main_image else [],
            "fulfillment_availability": [{
                "fulfillment_channel_code": "DEFAULT",
                "quantity": int(product.stock_quantity or 0),
            }],
        }

    # ==========================================
    # FLIPKART MAPPING & REQUIREMENTS
    # ==========================================
    @staticmethod
    def get_flipkart_missing_fields(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
    ) -> List[Dict[str, Any]]:
        """Identifies missing mandatory fields required by Flipkart Seller Hub."""
        missing = []
        cat_attrs = product.category_attributes or {}

        # 1. MRP (Maximum Retail Price)
        mrp = product.compare_at_price or cat_attrs.get("mrp")
        if not mrp or float(mrp) <= 0:
            missing.append({
                "field": "mrp",
                "label": "Maximum Retail Price (MRP)",
                "type": "number",
                "description": "Flipkart mandates printed MRP. Selling price must be <= MRP.",
                "required": True,
            })

        # 2. HSN Code
        if not cat_attrs.get("hsn_code"):
            missing.append({
                "field": "hsn_code",
                "label": "GST HSN Code",
                "type": "text",
                "description": "Required for Flipkart GST invoice generation.",
                "required": True,
            })

        # 3. Shipping Weight
        shipping = product.shipping_specs or {}
        if not (product.weight or shipping.get("shipping_weight_grams")):
            missing.append({
                "field": "shipping_weight",
                "label": "Dead Weight (Grams)",
                "type": "number",
                "description": "Required by Flipkart logistics partner for shipping tier calculation.",
                "required": True,
            })

        return missing

    @staticmethod
    def validate_for_flipkart(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
    ) -> Tuple[bool, List[str], List[str]]:
        """Validates product for Flipkart Seller API."""
        errors: List[str] = []
        warnings: List[str] = []

        title = (override.custom_title if override and override.custom_title else product.title) or ""
        if not title.strip():
            errors.append("Product Title is required for Flipkart.")

        price = (override.custom_price if override and override.custom_price is not None else product.base_price) or 0.0
        mrp = product.compare_at_price or 0.0
        if mrp and float(price) > float(mrp):
            errors.append(f"Selling price (₹{price}) cannot exceed MRP (₹{mrp}) on Flipkart.")

        missing_fields = ChannelMapper.get_flipkart_missing_fields(product, override)
        for mf in missing_fields:
            if mf.get("required"):
                errors.append(f"Flipkart missing field: {mf['label']}")

        return len(errors) == 0, errors, warnings

    @staticmethod
    def map_to_flipkart(
        product: Product,
        override: Optional[ProductChannelOverride] = None,
    ) -> Dict[str, Any]:
        """Maps master product to Flipkart Seller Hub listing payload."""
        price = (override.custom_price if override and override.custom_price is not None else product.base_price) or 0.0
        mrp = product.compare_at_price or price
        cat_attrs = product.category_attributes or {}
        packaging = product.packaging_specs or {}
        dims = packaging.get("box_dimensions") or product.dimensions or {}

        return {
            "sku_id": product.sku,
            "product_id": product.sku,
            "price": {
                "mrp": float(mrp),
                "selling_price": float(price),
                "currency": "INR",
            },
            "stock_details": {
                "available_stock": int(product.stock_quantity or 0),
            },
            "shipping_fees": {
                "local": 0,
                "zonal": 0,
                "national": 0,
            },
            "package_details": {
                "length": float(dims.get("length", 10)),
                "breadth": float(dims.get("width", 10)),
                "height": float(dims.get("height", 5)),
                "weight": float(product.weight or 0.5),
            },
            "tax_details": {
                "hsn": str(cat_attrs.get("hsn_code", "69120000")),
                "gst_percentage": int(cat_attrs.get("gst_percentage", 18)),
            },
        }

    # ==========================================
    # UNIVERSAL REQUIREMENTS CHECKER
    # ==========================================
    @staticmethod
    def check_all_channel_requirements(
        product: Product,
        channels: List[str],
        override: Optional[ProductChannelOverride] = None,
    ) -> Dict[str, Any]:
        """Analyzes master product against multiple channels and returns structured readiness."""
        results = {}

        for ch in channels:
            ch_lower = ch.lower()
            if ch_lower == "shopify":
                is_valid, errors, warnings = ChannelMapper.validate_for_shopify(product, override)
                results["shopify"] = {
                    "is_ready": is_valid,
                    "errors": errors,
                    "warnings": warnings,
                    "missing_fields": [],
                    "channel_name": "Shopify",
                }
            elif ch_lower == "woocommerce":
                is_valid, errors, warnings = ChannelMapper.validate_for_woocommerce(product, override)
                results["woocommerce"] = {
                    "is_ready": is_valid,
                    "errors": errors,
                    "warnings": warnings,
                    "missing_fields": [],
                    "channel_name": "WooCommerce",
                }
            elif ch_lower == "amazon":
                missing = ChannelMapper.get_amazon_missing_fields(product, override)
                is_valid, errors, warnings = ChannelMapper.validate_for_amazon(product, override)
                results["amazon"] = {
                    "is_ready": is_valid,
                    "errors": errors,
                    "warnings": warnings,
                    "missing_fields": missing,
                    "channel_name": "Amazon India",
                }
            elif ch_lower == "flipkart":
                missing = ChannelMapper.get_flipkart_missing_fields(product, override)
                is_valid, errors, warnings = ChannelMapper.validate_for_flipkart(product, override)
                results["flipkart"] = {
                    "is_ready": is_valid,
                    "errors": errors,
                    "warnings": warnings,
                    "missing_fields": missing,
                    "channel_name": "Flipkart",
                }
            elif ch_lower == "instagram":
                is_valid, errors, warnings = ChannelMapper.validate_for_instagram(product, override)
                results["instagram"] = {
                    "is_ready": is_valid,
                    "errors": errors,
                    "warnings": warnings,
                    "missing_fields": [],
                    "channel_name": "Instagram Professional",
                }

        return results


