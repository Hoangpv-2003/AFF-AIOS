from __future__ import annotations
from typing import Any, Dict, Optional
import os
import json
import httpx
import bs4
from email.message import EmailMessage

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        # Extract the recipient's email from the input data
        to_email = input_data.get("recipient")
        
        # Validate the to_email
        if not to_email:
            raise ValueError("'recipient' is required in input_data")

        # Define a function to send an email using httpx
        def send_email(to_email: str, subject: str, content: str):
            msg = EmailMessage()
            msg.set_content(content)
            msg["Subject"] = subject
            msg["From"]    = os.getenv("FROM_EMAIL", "")
            msg["To"]      = to_email
            
            with httpx.Client() as client:
                resp = client.post(
                    "https://email-sending-service.com/send-email",
                    json={
                        "from": msg["From"],
                        "to": msg["To"],
                        "subject": msg["Subject"],
                        "content": content
                    }
                )
                resp.raise_for_status()

        # Extract the email body and send status from the input data
        email_body = input_data.get("email_body", "")
        send_status = input_data.get("send_status", "")

        # Send an email with the provided email body if it's not empty
        if email_body:
            subject = "Daily Update Email"
            content = email_body
            
            # Handle potential exceptions when sending an email
            try:
                send_email(to_email, subject, content)
                
                # Return a successful response with the send status
                return {
                    "status": "success",
                    "send_status": send_status,
                    "summary": f"Email sent to {to_email}",
                }
            except httpx.HTTPStatusError as exc:
                return {"status": "error", "send_status": send_status, "summary": f"HTTP error: {exc.response.status_code}"}
        else:
            # Return a successful response with the send status
            return {
                "status": "success",
                "send_status": send_status,
                "summary": f"No email body provided. Skipping sending an email to {to_email}",
            }
    
    except Exception as exc:
        return {"status": "error", "send_status": "", "summary": str(exc)}
