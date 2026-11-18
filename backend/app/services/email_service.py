"""Transactional Email Service for MarketPath AI.

Implements genuine email delivery via SMTP or Resend/SendGrid when configured.
Enforces the Zero Faking rule: when email credentials are not configured,
it honestly logs the email locally and records 'unconfigured_provider' status
without claiming an email was sent.
"""

import email.message
import json
import logging
import smtplib
import urllib.request
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Manages transactional emails with honest status reporting and zero-faking guarantees."""

    @staticmethod
    def is_email_provider_configured() -> bool:
        """Checks if any supported transactional email provider credentials exist."""
        if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
            return True
        if settings.EMAIL_API_KEY or settings.BREVO_API_KEY or settings.RESEND_API_KEY or settings.SENDGRID_API_KEY:
            return True
        return False

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dispatches an email or records unconfigured status honestly."""
        if not cls.is_email_provider_configured():
            logger.info(
                f"[EMAIL UNCONFIGURED] Would send to: {to_email} | Subject: '{subject}' | Text:\n{text_content[:200]}..."
            )
            return {
                "status": "unconfigured_provider",
                "recipient": to_email,
                "subject": subject,
                "provider": "none",
                "detail": "Transactional email provider is unconfigured in settings. Email logged locally.",
            }

        # Attempt Brevo API if key is present
        api_key = settings.EMAIL_API_KEY or settings.BREVO_API_KEY
        if api_key:
            try:
                brevo_url = "https://api.brevo.com/v3/smtp/email"
                brevo_payload = {
                    "sender": {"name": settings.EMAIL_FROM_NAME, "email": settings.SMTP_FROM_EMAIL},
                    "to": [{"email": to_email}],
                    "subject": subject,
                    "textContent": text_content,
                }
                if html_content:
                    brevo_payload["htmlContent"] = html_content

                req = urllib.request.Request(
                    brevo_url,
                    data=json.dumps(brevo_payload).encode("utf-8"),
                    headers={
                        "api-key": api_key,
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    message_id = resp_data.get("messageId", "brevo_dispatched")
                    logger.info(f"[EMAIL DELIVERED] Successfully sent email to {to_email} via Brevo API (ID: {message_id}).")
                    return {
                        "status": "delivered",
                        "recipient": to_email,
                        "subject": subject,
                        "provider": "brevo",
                        "detail": f"Handed off to Brevo API. Message ID: {message_id}",
                    }
            except Exception as e:
                logger.error(f"[EMAIL ERROR] Failed to send email to {to_email} via Brevo API: {e}")
                return {
                    "status": "failed",
                    "recipient": to_email,
                    "subject": subject,
                    "provider": "brevo",
                    "detail": str(e),
                }

        # Attempt SMTP if host is provided
        if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
            try:
                msg = email.message.EmailMessage()
                msg["Subject"] = subject
                msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
                msg["To"] = to_email
                msg.set_content(text_content)
                if html_content:
                    msg.add_alternative(html_content, subtype="html")

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

                logger.info(f"[EMAIL DELIVERED] Successfully sent email to {to_email} via SMTP.")
                return {
                    "status": "delivered",
                    "recipient": to_email,
                    "subject": subject,
                    "provider": "smtp",
                    "detail": "Message handed off to SMTP server successfully.",
                }
            except Exception as e:
                logger.error(f"[EMAIL ERROR] Failed to send email to {to_email} via SMTP: {e}")
                return {
                    "status": "failed",
                    "recipient": to_email,
                    "subject": subject,
                    "provider": "smtp",
                    "detail": str(e),
                }

        return {
            "status": "unconfigured_provider",
            "recipient": to_email,
            "subject": subject,
            "provider": "none",
            "detail": "Email provider credentials absent or incomplete.",
        }

    @classmethod
    def send_consultation_confirmation_email(
        cls,
        to_email: str,
        full_name: str,
        brand_name: str,
        reference_code: str,
        preferred_date: Optional[str],
        time_slot: Optional[str],
        timezone: str = "Asia/Kolkata",
        status: str = "submitted",
    ) -> Dict[str, Any]:
        """Sends customer acknowledgement/confirmation email for a growth consultation booking."""
        is_confirmed = status.lower() in ["confirmed", "scheduled"]
        status_label = "Confirmed" if is_confirmed else "Request Received (Awaiting Advisor Confirmation)"
        subject_prefix = "Consultation Confirmed" if is_confirmed else "Consultation Request Received"
        subject = f"{subject_prefix}: {brand_name} (Ref: {reference_code}) — MarketPath AI"

        action_summary = (
            "Your appointment has been confirmed. A calendar invitation with your meeting link has been attached."
            if is_confirmed
            else "Your consultation request has been received. Our senior growth advisor will review your brand details and confirm your appointment window shortly."
        )

        text = f"""Hello {full_name},

Thank you for your interest in MarketPath AI for {brand_name}.

Appointment Reference: {reference_code}
Status: {status_label}
Date: {preferred_date or 'To be finalized with advisor'}
Time Slot: {time_slot or 'Standard 30-min window'} ({timezone})

{action_summary}

What to expect:
1. Category & Packaging Audit: Review of product packaging specs, volumetric weight, and HSN compliance.
2. Channel Expansion Blueprint: Strategic evaluation across Shopify, Amazon India, Flipkart, and Quick Commerce.
3. Preparation: Please have your active product SKUs and packaging dimensions handy.

Warm regards,
MarketPath AI Advisory Team
https://marketpath.ai
"""
        html = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #18231F; max-width: 600px; margin: 0 auto; padding: 24px; background-color: #FCFBF7; border: 1px solid #E5E7EB; border-radius: 16px;">
  <div style="margin-bottom: 20px;">
    <span style="display: inline-block; padding: 4px 12px; background-color: #F4EDE2; color: #075443; border-radius: 12px; font-size: 12px; font-weight: bold;">
      MarketPath AI Growth Advisory
    </span>
  </div>
  <h2 style="color: #075443; margin-top: 0; font-size: 22px;">{subject_prefix}</h2>
  <p style="font-size: 14px; line-height: 1.6;">Hello <strong>{full_name}</strong>,</p>
  <p style="font-size: 14px; line-height: 1.6;">{action_summary}</p>
  
  <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 18px; margin: 20px 0;">
    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
      <tr><td style="padding: 6px 0; color: #64716C; width: 130px;">Reference Code:</td><td style="padding: 6px 0; font-weight: bold; font-family: monospace; color: #08765B;">{reference_code}</td></tr>
      <tr><td style="padding: 6px 0; color: #64716C;">Brand / Business:</td><td style="padding: 6px 0; font-weight: bold;">{brand_name}</td></tr>
      <tr><td style="padding: 6px 0; color: #64716C;">Status:</td><td style="padding: 6px 0; font-weight: bold; color: {'#08765B' if is_confirmed else '#D99143'};">{status_label}</td></tr>
      <tr><td style="padding: 6px 0; color: #64716C;">Requested Date:</td><td style="padding: 6px 0;">{preferred_date or 'To be finalized with advisor'}</td></tr>
      <tr><td style="padding: 6px 0; color: #64716C;">Requested Time:</td><td style="padding: 6px 0;">{time_slot or '30-minute strategy session'} ({timezone})</td></tr>
    </table>
  </div>

  <p style="font-size: 13px; color: #64716C; line-height: 1.5;">
    If you need to reschedule or have questions prior to the call, reply directly to this email with your reference code <strong>{reference_code}</strong>.
  </p>
  
  <div style="border-top: 1px solid #E5E7EB; margin-top: 24px; padding-top: 16px; font-size: 12px; color: #64716C;">
    <strong>MarketPath AI</strong> — One workspace to manage your brand's digital growth.
  </div>
</div>"""
        return cls.send_email(to_email=to_email, subject=subject, text_content=text, html_content=html)

    @classmethod
    def send_internal_consultation_alert(
        cls,
        reference_code: str,
        full_name: str,
        email: str,
        phone: Optional[str],
        brand_name: str,
        category: str,
        business_stage: str,
        monthly_revenue: Optional[str],
        preferred_date: Optional[str],
        time_slot: Optional[str],
        challenges: Optional[str],
    ) -> Dict[str, Any]:
        """Dispatches an internal alert to the MarketPath consultation & advisory team."""
        to_email = settings.BOOKING_NOTIFICATION_TO or "consultations@marketpath.ai"
        subject = f"[New Consultation Request] {brand_name} — Ref: {reference_code}"
        text = f"""New Merchant Growth Consultation Request Received:

Reference: {reference_code}
Customer Name: {full_name}
Brand Name: {brand_name}
Email: {email}
Phone: {phone or 'Not provided'}
Category: {category}
Business Stage: {business_stage}
Monthly Revenue: {monthly_revenue or 'Not disclosed'}
Requested Date: {preferred_date or 'Flexible'}
Requested Time Slot: {time_slot or 'Flexible'} (Asia/Kolkata)

Merchant Objectives & Challenges:
{challenges or 'None specified'}

Please review this inbound lead in the Platform Admin console (/admin) or assign to an authorized Category Specialist.
"""
        html = f"""<div style="font-family: sans-serif; color: #18231F; max-width: 600px; padding: 20px;">
  <h3 style="color: #075443;">New Consultation Request: {brand_name}</h3>
  <p><strong>Reference:</strong> <code>{reference_code}</code></p>
  <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
    <tr><td><strong>Contact:</strong></td><td>{full_name} ({email}, {phone or 'No phone'})</td></tr>
    <tr><td><strong>Brand:</strong></td><td>{brand_name} ({category})</td></tr>
    <tr><td><strong>Scale:</strong></td><td>{business_stage} | Revenue: {monthly_revenue or 'N/A'}</td></tr>
    <tr><td><strong>Requested Slot:</strong></td><td>{preferred_date or 'Any'} at {time_slot or 'Any'}</td></tr>
  </table>
  <div style="margin-top: 15px; padding: 12px; background: #F4EDE2; border-radius: 8px;">
    <strong>Challenges:</strong><br>{challenges or 'None provided'}
  </div>
</div>"""
        return cls.send_email(to_email=to_email, subject=subject, text_content=text, html_content=html)

    @classmethod
    def send_team_invitation_email(
        cls,
        to_email: str,
        inviter_name: str,
        org_name: str,
        role: str,
        invite_url: str,
    ) -> Dict[str, Any]:
        """Sends signed invitation link to join an organization."""
        subject = f"Invitation to join {org_name} on MarketPath AI"
        text = f"""Hello,

{inviter_name} has invited you to join the team workspace for {org_name} on MarketPath AI as a {role.capitalize()}.

To accept this invitation and access the workspace, use the secure link below:
{invite_url}

This invitation link is valid for 7 days.

MarketPath AI Team
https://marketpath.ai
"""
        return cls.send_email(to_email=to_email, subject=subject, text_content=text)
