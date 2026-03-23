from __future__ import annotations

import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any, Dict, Optional

import httpx


def _send_with_resend(to_email: str, subject: str, content: str) -> Dict[str, Any]:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email = os.getenv("RESEND_FROM_EMAIL", "").strip()
    if not api_key or not from_email:
        return {
            "sent": False,
            "provider": "resend",
            "error": "missing_resend_credentials",
        }

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "text": content,
            },
            timeout=12.0,
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        return {
            "sent": True,
            "provider": "resend",
            "id": payload.get("id"),
        }
    except Exception as exc:
        return {"sent": False, "provider": "resend", "error": str(exc)}


def _send_with_smtp(to_email: str, subject: str, content: str) -> Dict[str, Any]:
    host = os.getenv("SMTP_HOST", "").strip()
    user = os.getenv("SMTP_USER", "").strip()
    password = (
        os.getenv("SMTP_PASSWORD", "").strip()
        or os.getenv("SMTP_PASS", "").strip()
    )
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip() or user
    port_raw = os.getenv("SMTP_PORT", "587").strip()

    if not host or not user or not password or not from_email:
        return {
            "sent": False,
            "provider": "smtp",
            "error": "missing_smtp_credentials",
        }

    try:
        port = int(port_raw)
    except Exception:
        port = 587

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(content)

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=15) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)
        return {"sent": True, "provider": "smtp"}
    except Exception as exc:
        return {"sent": False, "provider": "smtp", "error": str(exc)}


def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    payload = dict(input_data or {})
    recipient = str(payload.get("recipient") or payload.get("to_email") or "").strip()
    report = str(payload.get("report") or payload.get("summary") or "").strip()
    subject = str(payload.get("subject") or "AAF-AIOS Report").strip()

    if not recipient:
        return {
            "status": "error",
            "summary": "Thiếu email người nhận.",
            "error_reason": "missing_recipient",
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }
    if not report:
        return {
            "status": "error",
            "summary": "Không có nội dung báo cáo để gửi.",
            "error_reason": "missing_report_content",
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    provider = str(payload.get("provider") or os.getenv("EMAIL_PROVIDER", "")).strip().lower()
    if not provider:
        return {
            "status": "error",
            "summary": "Thiếu cấu hình provider email.",
            "error_reason": "missing_email_provider",
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    if provider == "smtp":
        result = _send_with_smtp(recipient, subject, report)
    elif provider == "resend":
        result = _send_with_resend(recipient, subject, report)
    else:
        return {
            "status": "error",
            "summary": "Provider email khong duoc ho tro.",
            "error_reason": "unsupported_email_provider",
            "email": {"provider": provider},
            "to": recipient,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "status": "success" if result.get("sent") else "error",
        "summary": (
            f"Đã gửi email cho {recipient}."
            if result.get("sent")
            else f"Không gửi được email cho {recipient}."
        ),
        "email": result,
        "to": recipient,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
