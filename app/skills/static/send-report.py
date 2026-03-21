from __future__ import annotations

import json
import os
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, Optional


def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        recipient = str(input_data.get("recipient") or input_data.get("to_email") or "").strip()
        if not recipient:
            return {
                "status": "error",
                "summary": "Missing recipient.",
                "error_reason": "recipient is required",
            }

        report = input_data.get("report")
        summary_text = input_data.get("summary_text")
        if not summary_text:
            if isinstance(report, dict):
                summary_text = json.dumps(report, ensure_ascii=False, indent=2)
            elif report is not None:
                summary_text = str(report)
            else:
                results = input_data.get("results")
                if isinstance(results, list) and results:
                    lines = []
                    for item in results[:5]:
                        if isinstance(item, dict):
                            title = str(item.get("title") or "(no title)")
                            content = str(item.get("content") or "")
                            lines.append(f"- {title}: {content[:180]}")
                        else:
                            lines.append(f"- {str(item)[:180]}")
                    summary_text = "Report summary:\n" + "\n".join(lines)
                else:
                    summary_text = "No report content provided."

        smtp_host = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD")
        if not all([smtp_host, smtp_user, smtp_pass]):
            return {
                "status": "error",
                "summary": "Missing SMTP configuration.",
                "error_reason": "SMTP_HOST/SMTP_USER/SMTP_PASS is required",
            }

        msg = EmailMessage()
        msg["Subject"] = str(input_data.get("subject") or "Revenue Report")
        msg["From"] = smtp_user
        msg["To"] = recipient
        msg.set_content(summary_text)

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

        return {
            "status": "success",
            "summary": "Report sent successfully.",
            "to": recipient,
        }
    except Exception as exc:
        return {
            "status": "error",
            "summary": "Failed to send report.",
            "error_reason": str(exc),
        }