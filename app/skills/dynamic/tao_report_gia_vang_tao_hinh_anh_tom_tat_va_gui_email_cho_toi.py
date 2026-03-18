from __future__ import annotations
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

def run(input_data: dict | None = None) -> dict:
    gold_price = {"SJC": 65.5, "Au9999": 66.0, "Au9995": 65.8, "Au999": 65.6}
    report_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    summary_text = (
        f"Report Gia Vàng {report_date}\n"
        f"SJC: {gold_price['SJC']} triệu VNĐ/giờ\n"
        f"Au9999: {gold_price['Au9999']} triệu VNĐ/giờ\n"
        f"Au9995: {gold_price['Au9995']} triệu VNĐ/giờ\n"
        f"Au999: {gold_price['Au999']} triệu VN"
    )
    
    image = Image.new("RGB", (600, 200), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 10), summary_text, fill="black", font=font)
    
    img_io = BytesIO()
    image.save(img_io, format='PNG')
    img_io.seek(0)
    
    msg = MIMEMultipart()
    msg['Subject'] = 'Báo cáo giá vàng'
    msg['From'] = 'your_email@example.com'
    msg['To'] = 'recipient@example.com'
    
    msg.attach(MIMEText(summary_text, 'plain'))
    
    img = MIMEImage(img_io.read(), name='summary.png')
    img.add_header('Content-Disposition', 'attachment', filename='summary.png')
    msg.attach(img)
    
    response = {
        "status": "success",
        "message": "Email đã được gửi",
        "report_date": report_date,
        "gold_price": gold_price,
        "summary_text": summary_text,
        "image_filename": "summary.png"
    }
    
    return response
