from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx
import pandas as pd
import matplotlib.pyplot as plt
import base64
import smtplib
from email.message import EmailMessage

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        url: str      = input_data.get("url", os.getenv("SOCcer_API_URL", ""))
        api_key: str  = os.getenv("SOCcer_API_KEY", "")
        
        if not url:
            raise ValueError("'url' is required in input_data or SOCcer_API_URL env var")
        
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers={"Authorization": f"Bearer {api_key}"})
            resp.raise_for_status()
            
            data: dict = resp.json()
            results_df = pd.DataFrame(data["results"])
            
            # Create a bar chart
            fig, ax = plt.subplots()
            ax.bar(results_df['Team'], results_df['Score'])
            img_data = base64.b64encode(fig.canvas.to_image().tobytes())
            
            # Send email with the chart
            to_email: str = input_data.get("to_email", "tuanm7530@gmail.com")
            subject: str  = "Daily Soccer Results"
            content: str  = f"Hello,\n\nHere are today's soccer results:\n{results_df.to_string()}\n\nBest,\n{input_data.get('sender', 'Python Skill')}"
            msg = EmailMessage()
            msg.set_content(content)
            msg["Subject"] = subject
            msg["From"]    = input_data.get("from_email", "soccer-results@example.com")
            msg["To"]      = to_email
            
            with smtplib.SMTP(os.getenv("SMTP_HOST", ""), int(os.getenv("SMTP_PORT", 587))) as smtp:
                smtp.starttls()
                smtp.login(input_data.get("smtp_user"), input_data.get("smtp_password"))
                smtp.send_message(msg)
                
        return {
            "status": "success",
            "summary": f"Results sent to {to_email}",
            "image_url": f"data:image/png;base64,{img_data.decode()}",
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc)}
