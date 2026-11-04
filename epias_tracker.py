import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import requests

def fetch_epias_ptf():
    target_date = datetime.now().strftime('%Y-%m-%d')
    url = f"https://seffaflik.epias.com.tr/transparency/service/market-clearing-price/ptf?startDate={target_date}&endDate={target_date}"
    
    hourly_data = []
    data_source_name = "Gün Öncesi Piyasası - Piyasa Takas Fiyatı (PTF)"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            
            items = []
            if isinstance(result, list):
                items = result
            elif "body" in result:
                body = result["body"]
                if isinstance(body, list):
                    items = body
                elif isinstance(body, dict):
                    items = body.get("items", []) or body.get("entofMcpList", [])
            elif "items" in result:
                items = result["items"]

            for item in items:
                date_time = item.get("date", "") or item.get("dateTime", "")
                price = item.get("ptf", 0.0) or item.get("price", 0.0) or item.get("congestedPtf", 0.0)
                
                if "T" in str(date_time):
                    hour_str = str(date_time).split("T")[1][:5]
                else:
                    hour_str = str(date_time)[-8: -3] if len(str(date_time)) >= 8 else "00:00"
                    
                hourly_data.append({
                    "hour": hour_str,
                    "price": float(price)
                })
    except Exception as e:
        print(f"API Bağlantı Hatası: {e}")

    return target_date, hourly_data, data_source_name

def send_email(target_date, data, source_name):
    sender_email = os.environ.get("MAIL_USER")
    sender_password = os.environ.get("MAIL_PASS")
    receiver_email = "selcuk.bahadir.61@gmail.com"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"EPİAŞ Raporu [{source_name}] - {target_date}"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    if not data:
        html_body = f"<h3>{target_date} için {source_name} verisi henüz listelenemedi.</h3>"
    else:
        html_body = f"<div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;'>"
        html_body += f"<h2 style='color: #1a73e8;'>{target_date} Tarihli Rapor</h2>"
        html_body += f"<p><b>Veri Kaynağı / Piyasası:</b> <span style='color: #d93025;'>{source_name}</span></p>"
        html_body += "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; width: 100%; text-align: left;'>"
        html_body += "<tr style='background-color: #f2f2f2; color: #333;'><th>Saat Dilimi</th><th>PTF (TL / MWh)</th></tr>"
        for row in data:
            html_body += f"<tr><td><b>{str(row['hour'])}</b></td><td>{row['price']:,.2f} TL</td></tr>"
        html_body += "</table>"
        html_body += "<p style='font-size: 12px; color: #666; margin-top: 20px;'>Bu rapor GitHub Actions üzerinden otomatik olarak gönderilmiştir.</p>"
        html_body += "</div>"

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("E-posta başarıyla gönderildi.")
    except Exception as e:
        print(f"E-posta gönderilemedi: {e}")

if __name__ == "__main__":
    date, data, source = fetch_epias_ptf()
    send_email(date, data, source)
