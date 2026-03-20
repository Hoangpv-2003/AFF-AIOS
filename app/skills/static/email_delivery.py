import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

def run(input_data: dict = None, **kwargs) -> dict:
    input_data = input_data or {}
    # Combine input_data and kwargs for flexibility
    data = {**input_data, **kwargs}
    
    results = data.get('results')
    recipient = data.get('recipient', 'tuanm7530@gmail.com')

    try:
        # Email configuration followings prompt_templates.py standards
        smtp_server = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        sender_email = os.environ.get('SMTP_USER')
        sender_password = os.environ.get('SMTP_PASSWORD')

        if not all([smtp_server, smtp_port, sender_email, sender_password]):
            return {'status': 'error', 'summary': f'Missing email configuration: {{"host": {bool(smtp_server)}, "port": {bool(smtp_port)}, "user": {bool(sender_email)}, "pass": {bool(sender_password)}}}'}

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = 'VinFast 2025 Revenue Report'

        # Add results as plain text body
        body = results if isinstance(results, str) else json.dumps(results, indent=2, ensure_ascii=False)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Connect to SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, msg.as_string())

        return {'status': 'success', 'summary': f'Email sent successfully to {recipient}'}
    except Exception as e:
        return {'status': 'error', 'summary': str(e)}