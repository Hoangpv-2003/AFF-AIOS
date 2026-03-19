from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
import pandas as pd

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        api_key: str  = os.getenv("API_KEY_GASOLINE_PRICES", "")
        
        if not api_key:
            raise ValueError("'api_key' is required for gasoline prices API")
        
        url: str      = "https://api.example.com/gasoline-prices"
        method: str   = "GET"
        headers: dict = {}
        payload: dict = {}
        timeout: int  = 15

        with httpx.Client(timeout=timeout) as client:
            if method == "GET":
                resp = client.get(url, headers=headers, params=payload)
            else:
                resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

        data: dict = resp.json()
        
        # Process the API response using pandas
        gasoline_prices: pd.DataFrame = pd.DataFrame(data["prices"])
        
        email_to: str  = input_data.get("email", "")
        email_subject: str = "Daily Gasoline Prices Update"
        email_content: str = f"Gasoline prices update for today:\n{gasoline_prices.to_string(index=False)}"

        if not email_to:
            raise ValueError("'email' is required to send email")

        # Send the email using smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg.set_content(email_content)
        msg["Subject"] = email_subject
        msg["From"]    = "your_email@example.com"
        msg["To"]      = email_to

        with smtplib.SMTP("smtp.example.com", 587) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            smtp.send_message(msg)

        return {
            "status": "success",
            "gasoline_prices": gasoline_prices.to_dict(orient="records"),
            "email_status": True,
            "summary": f"Email sent to {email_to} with daily gasoline prices update",
        }
    
    except httpx.HTTPStatusError as exc:
        return {"status": "error", "data": {}, "summary": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "data": {}, "summary": str(exc)}
