from __future__ import annotations
from typing import Any, Dict, Optional
import smtplib
import email.parser


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        result: str = input_data.get("result", "")
        recipient_email: str = "phamvanhoang12abm@gmail.com"
        
        if not all([result, recipient_email]):
            raise ValueError("'result' and 'recipient_email' must be provided in input_data")

        msg = email.parser.Parser().parsestr(f"""
Subject: Answer Today
Content-Type: text/html

<!DOCTYPE html>
<html>
<head>
    <title>Answer Today</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
        }}
    </style>
</head>
<body>
    <h1>Answer for Today:</h1>
    <p>{result}</p>
</body>
</html>
""")

        msg.add_header("To", recipient_email)

        host: str     = "smtp.gmail.com"
        port: int     = 465
        user: str     = "your-email@gmail.com"
        pw: str       = "your-password"

        if not all([host, user, pw]):
            raise ValueError("'host', 'user', and 'pw' must be provided in input_data")

        # Send Email
        with smtplib.SMTP_SSL(host, port) as smtp:
            smtp.login(user, pw)
            smtp.send_message(msg)

        return {
            "status": "success",
            "summary": f"Email sent to {recipient_email}"
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
