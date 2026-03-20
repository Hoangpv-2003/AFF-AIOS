import os, smtplib
from email.message import EmailMessage
def run(input_data=None, **kwargs):
    recipient = input_data.get("recipient")
    host, port = os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", 465))
    user = os.getenv("SMTP_USER")
    pw = os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD")
    msg = EmailMessage()
    msg.set_content(str(input_data.get("results")))
    msg["Subject"] = "Báo cáo doanh thu VinFast 2025"
    msg["From"], msg["To"] = user, recipient
    if port == 465:
        with smtplib.SMTP_SSL(host, port) as s:
            s.login(user, pw)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(msg)
    return {"status": "success", "summary": "sent"}