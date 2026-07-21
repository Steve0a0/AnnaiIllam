"""Email service — Resend integration.

Usage:
    from app.services.email_service import send_payment_receipt

    # Fire-and-forget inside a BackgroundTask:
    background_tasks.add_task(
        send_payment_receipt,
        payment_id=payment.id,
        ...
    )

Environment variables (add to .env):
    RESEND_API_KEY=re_xxxxxxxxxxxx
    RESEND_FROM_EMAIL=invoices@annaiillam.com   # must be a verified Resend domain
    RESEND_FROM_NAME=Annai Illam
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Payment receipt HTML template
# ---------------------------------------------------------------------------

def _build_payment_receipt_html(
    *,
    invoice_number: str,
    payment_date: str,
    client_name: str,
    requirement_category: str,
    requirement_subcategory: str | None,
    work_location: str,
    city: str,
    state: str,
    start_date: str,
    duration_days: int,
    payment_model: str,
    amount: int,
    reference_note: str | None,
) -> str:
    subcategory_row = (
        f"<tr><td style='{TD_LABEL}'>Role</td>"
        f"<td style='{TD_VALUE}'>{requirement_subcategory}</td></tr>"
        if requirement_subcategory else ""
    )
    ref_row = (
        f"<tr><td style='{TD_LABEL}'>Reference</td>"
        f"<td style='{TD_VALUE}'>{reference_note}</td></tr>"
        if reference_note else ""
    )
    model_label = {
        "advance": "Advance Payment",
        "full": "Full Payment",
        "balance": "Balance Payment",
    }.get(payment_model, payment_model.replace("_", " ").title())

    amount_inr = f"₹{amount:,}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Payment Receipt — {invoice_number}</title>
</head>
<body style="margin:0;padding:0;background:#F5F5F4;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F5F4;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:12px;overflow:hidden;
                    box-shadow:0 2px 12px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:#0D2E1E;padding:32px 40px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <p style="margin:0;font-size:22px;font-weight:700;color:#ffffff;">
                    Annai Illam
                  </p>
                  <p style="margin:4px 0 0;font-size:13px;color:rgba(255,255,255,0.6);">
                    Staffing &amp; Manpower Solutions
                  </p>
                </td>
                <td align="right">
                  <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.55);">PAYMENT RECEIPT</p>
                  <p style="margin:4px 0 0;font-size:20px;font-weight:700;color:#25A263;">
                    {invoice_number}
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:32px 40px;">

            <!-- Greeting -->
            <p style="margin:0 0 24px;font-size:15px;color:#44403C;line-height:1.6;">
              Dear <strong>{client_name}</strong>,<br/>
              Thank you for your payment. Please find your receipt details below.
            </p>

            <!-- Payment summary card -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#F0FDF4;border:1px solid #86EFAC;
                          border-radius:10px;margin-bottom:28px;">
              <tr>
                <td style="padding:20px 24px;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="font-size:13px;color:#15803D;font-weight:600;
                                 padding-bottom:6px;">
                        PAYMENT CONFIRMED
                      </td>
                      <td align="right" style="font-size:24px;font-weight:700;color:#0D2E1E;">
                        {amount_inr}
                      </td>
                    </tr>
                    <tr>
                      <td style="font-size:13px;color:#78716C;">{model_label}</td>
                      <td align="right" style="font-size:13px;color:#78716C;">{payment_date}</td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>

            <!-- Job details table -->
            <p style="margin:0 0 10px;font-size:12px;font-weight:700;
                      color:#78716C;letter-spacing:1px;">
              JOB DETAILS
            </p>
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border:1px solid #E7E5E4;border-radius:10px;
                          border-collapse:separate;border-spacing:0;
                          overflow:hidden;margin-bottom:28px;">
              <tr>
                <td style="{TD_LABEL}">Service</td>
                <td style="{TD_VALUE}">{requirement_category}</td>
              </tr>
              {subcategory_row}
              <tr>
                <td style="{TD_LABEL}">Location</td>
                <td style="{TD_VALUE}">{work_location}, {city}, {state}</td>
              </tr>
              <tr>
                <td style="{TD_LABEL}">Start date</td>
                <td style="{TD_VALUE}">{start_date}</td>
              </tr>
              <tr>
                <td style="{TD_LABEL}">Duration</td>
                <td style="{TD_VALUE}">{duration_days} {'day' if duration_days == 1 else 'days'}</td>
              </tr>
              {ref_row}
            </table>

            <!-- Footer note -->
            <p style="margin:0;font-size:13px;color:#78716C;line-height:1.7;">
              This payment receipt is not a GST tax invoice.
              For any questions please contact us at
              <a href="mailto:support@annaiillam.com"
                 style="color:#1A6640;text-decoration:none;">support@annaiillam.com</a>.
            </p>

          </td>
        </tr>

        <!-- Footer bar -->
        <tr>
          <td style="background:#F5F5F4;padding:16px 40px;border-top:1px solid #E7E5E4;">
            <p style="margin:0;font-size:11px;color:#A8A29E;text-align:center;">
              © {datetime.now(UTC).year} Annai Illam · Staffing &amp; Manpower Solutions
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


# Shared cell styles (used inside the f-string above)
TD_LABEL = (
    "padding:12px 16px;font-size:13px;color:#78716C;font-weight:600;"
    "background:#FAFAF9;border-bottom:1px solid #E7E5E4;width:36%;"
)
TD_VALUE = (
    "padding:12px 16px;font-size:13px;color:#1C1917;"
    "border-bottom:1px solid #E7E5E4;"
)


# ---------------------------------------------------------------------------
# Public send function
# ---------------------------------------------------------------------------

def send_payment_receipt(
    *,
    to_email: str,
    client_name: str,
    payment_id: int,
    payment_date: datetime,
    payment_model: str,
    amount: int,
    reference_note: str | None,
    requirement_category: str,
    requirement_subcategory: str | None,
    work_location: str,
    city: str,
    state: str,
    start_date: str,
    duration_days: int,
) -> None:
    """Send a payment confirmation receipt (not a GST tax invoice).

    Uses Gmail SMTP if GMAIL_USER + GMAIL_APP_PASSWORD are set.
    Falls back to Resend if RESEND_API_KEY is set.
    Silently skips if neither is configured.
    """
    from app.core.config import settings  # lazy import to avoid circular

    invoice_number = f"RCT-{payment_id:05d}"
    payment_date_str = payment_date.strftime("%d %b %Y")
    start_date_str = _format_date(start_date)
    subject = f"Payment Confirmed — {invoice_number} | Annai Illam"

    html = _build_payment_receipt_html(
        invoice_number=invoice_number,
        payment_date=payment_date_str,
        client_name=client_name,
        requirement_category=requirement_category,
        requirement_subcategory=requirement_subcategory,
        work_location=work_location,
        city=city,
        state=state,
        start_date=start_date_str,
        duration_days=duration_days,
        payment_model=payment_model,
        amount=amount,
        reference_note=reference_note,
    )

    if settings.gmail_user and settings.gmail_app_password:
        _send_via_gmail(settings, to_email, subject, html, payment_id)
    elif settings.resend_api_key:
        _send_via_resend(settings, to_email, subject, html, payment_id)
    else:
        logger.info(
            "No email provider configured — skipping payment receipt for payment #%s", payment_id
        )


def send_tax_invoice(
    *, to_email: str, client_name: str, invoice_id: int, invoice_number: str, html: str
) -> None:
    """Email the exact immutable HTML stored on the issued tax invoice."""
    from app.core.config import settings

    subject = f"Tax Invoice {invoice_number} | Annai Illam"
    if settings.gmail_user and settings.gmail_app_password:
        _send_via_gmail(settings, to_email, subject, html, invoice_id)
    elif settings.resend_api_key:
        _send_via_resend(settings, to_email, subject, html, invoice_id)
    else:
        logger.info("No email provider configured - skipping tax invoice #%s", invoice_id)


def _send_via_gmail(
    settings: object,
    to_email: str,
    subject: str,
    html: str,
    payment_id: int,
) -> None:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.resend_from_name} <{settings.gmail_user}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.gmail_user, settings.gmail_app_password)
            server.sendmail(settings.gmail_user, to_email, msg.as_string())

        logger.info(
            "Invoice email sent for payment #%s → %s (via Gmail SMTP)",
            payment_id, to_email,
        )
    except Exception:
        logger.exception("Failed to send invoice email (Gmail SMTP) for payment #%s", payment_id)


def _send_via_resend(
    settings: object,
    to_email: str,
    subject: str,
    html: str,
    payment_id: int,
) -> None:
    try:
        import resend

        resend.api_key = settings.resend_api_key
        from_addr = f"{settings.resend_from_name} <{settings.resend_from_email}>"

        params: resend.Emails.SendParams = {
            "from": from_addr,
            "to": [to_email],
            "subject": subject,
            "html": html,
        }
        response = resend.Emails.send(params)
        logger.info(
            "Invoice email sent for payment #%s → %s (resend id: %s)",
            payment_id, to_email, response.get("id"),
        )
    except Exception:
        logger.exception("Failed to send invoice email (Resend) for payment #%s", payment_id)


def _format_date(value: str) -> str:
    """Format ISO date string to '05 Jun 2026'."""
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        return value
