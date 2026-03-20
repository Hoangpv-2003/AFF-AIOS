import os
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime

async def fetch_vinfast_revenue():
    """Fetch VinFast's 2025 revenue using Tavily API"""
    tavily_api_key = os.getenv('TAVILY_API_KEY')
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY environment variable is required")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.tavily.com/v1/search",
            headers={
                "Authorization": f"Bearer {tavily_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "query": "Báo cáo tài chính VinFast 2025 doanh thu lợi nhuận chính thức",
                "max_results": 1,
                "search_type": "web_search"
            }
        )

        response.raise_for_status()
        results = response.json().get('results', [])
        
        if not results:
            raise ValueError("Không tìm thấy thông tin doanh thu VinFast 2025")

        # Extract numerical data from first result
        content = results[0].get('content', '')
        revenue_match = None
        
        # Look for patterns like 'Doanh thu 2025: 10.5 tỷ USD'
        revenue_pattern = r'\bDoanh thu\s*2025:\s*(\d+\.?\d*)\s*(tỷ|triệu|USD)\b'
        revenue_match = re.search(revenue_pattern, content, re.IGNORECASE)
        
        if not revenue_match:
            raise ValueError("Không thể trích xuất số liệu doanh thu từ kết quả tìm kiếm")
        
        amount = revenue_match.group(1)
        currency = revenue_match.group(2).upper()
        
        return {
            'amount': amount,
            'currency': currency,
            'source': results[0].get('url', ''),
            'timestamp': datetime.now().isoformat()
        }

def send_email_report(results):
    """Send revenue report via email to tuanm7530@gmail.com"""
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    
    if not all([smtp_host, smtp_user, smtp_pass]):
        raise ValueError("SMTP credentials are missing in environment variables")
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = 'tuanm7530@gmail.com'
    msg['Subject'] = f"Báo cáo doanh thu VinFast 2025 ({results['timestamp']})"
    
    body = f""
    body += f"Kết quả tìm kiếm: {results['source']}
"
    body += f"Doanh thu 2025: {results['amount']} {results['currency']}
"
    body += ""
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(host=smtp_host, port=smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise

async def main():
    """Main function to execute the revenue report process"""
    try:
        results = await fetch_vinfast_revenue()
        send_email_report(results)
        print("Process completed successfully")
    except Exception as e:
        print(f"Error in process: {str(e)}")
        raise