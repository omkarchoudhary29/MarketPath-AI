"""PII and Commercial Privacy Sanitization Module.

Protects seller confidentiality by sanitizing founder personal phone numbers,
personal emails, private margins/cost prices, and financial data before
briefs are exposed to external marketing agencies and partners.
"""

import re
from typing import Any, Dict, List, Optional


def mask_email(email: Optional[str]) -> str:
    """Masks an email address: ananya.deshmukh@brand.in -> a***@brand.in."""
    if not email or "@" not in email:
        return "[Confidential]"
    local_part, domain = email.split("@", 1)
    if len(local_part) <= 2:
        masked_local = local_part[0] + "***"
    else:
        masked_local = local_part[:2] + "***" + local_part[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: Optional[str]) -> str:
    """Masks a phone number: +91 9876543210 -> +91 ******3210."""
    if not phone:
        return "[Verified Brand Founder]"
    clean = re.sub(r"[^\d+]", "", phone)
    if len(clean) >= 6:
        return clean[:3] + "******" + clean[-4:]
    return "[Protected Contact]"


def sanitize_client_brief(brief_data: Dict[str, Any]) -> Dict[str, Any]:
    """Strips founder PII and commercial financial margins from client briefs before agency portal view."""
    sanitized = dict(brief_data)

    # 1. Strip or mask founder personal contact
    if "founder_phone" in sanitized:
        sanitized["founder_phone"] = mask_phone(sanitized.get("founder_phone"))
    if "founder_email" in sanitized:
        sanitized["founder_email"] = mask_email(sanitized.get("founder_email"))
    if "personal_email" in sanitized:
        sanitized["personal_email"] = mask_email(sanitized.get("personal_email"))

    # 2. Redact internal commercial costs and margins
    for private_key in [
        "cost_price",
        "margin_percentage",
        "supplier_details",
        "raw_cost",
        "bank_account",
        "gstin_full",
    ]:
        sanitized.pop(private_key, None)

    # 3. Add explicit sanitization guarantee flag
    sanitized["_pii_sanitized"] = True
    sanitized["contact_protocol"] = "Communication routed via MarketPath Agency Connect Desk"

    return sanitized


def sanitize_founder_quote_request(quote_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes quote inquiry for agency consumption."""
    sanitized = dict(quote_data)

    # Mask sender identity
    if "contact_email" in sanitized:
        sanitized["contact_email"] = mask_email(sanitized.get("contact_email"))
    if "contact_phone" in sanitized:
        sanitized["contact_phone"] = mask_phone(sanitized.get("contact_phone"))

    # Mask specific financial margins
    sanitized.pop("internal_notes", None)
    sanitized.pop("billing_address", None)
    sanitized.pop("payment_method_id", None)

    return sanitized

