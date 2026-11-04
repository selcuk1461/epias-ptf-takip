import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import requests

def fetch_epias_ptf():
    target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    url = f"https://seffaflik.epias.com.tr/transparency/service/market-clearing-price/ptf?startDate={target_date}&endDate={target_date}"
    
    hourly_data = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            items = []
            if "body" in result and isinstance(result["body"], list):
                items = result["body"]
            elif "items" in result and isinstance(result["items"], list):
                items = result["items"]
            elif isinstance(result, list):
                items = result
                
            for item in items:
                date_time = item.get("date", "")
                price = item.get("ptf", 0.0)
                if price == 0.0:
                    price = item.get("price", 0.0)
                
                if "T" in str(date_time):
                    hour_str = str(date_time).split("T")[1][:5]
                else:
                    hour_str = "00:00"
                    
                hourly_data.append({
                    "hour": hour_str,
                    "price": float(price)
                })
    except Exception as e:
        print(f"API Bağlantı Hatası: {e}")

    if not hourly_data:
        today_date = datetime.now().strftime('%Y-%m-%d')
        url_today = f"https://seffaflik.epias.com.tr/transparency/service/market-clearing-price/ptf?startDate={today_date}&endDate={today_date}"
        try:
            response = requests.get(url_today, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if response.status_code == 200:
                result = response.json()
                items = result.get("body", []) or result.get("items", [])
                for item in items:
                    date_time = item.get("date", "")
                    price = item.get("ptf", 0.0) or item.get("price", 0.0)
                    hour_str = str(date_time).split("T")[1][:5] if "T" in str(date_time) else "00:00"
                    hourly_data.append({
                        "hour": hour_str,
                        "price": float(price)
                    })
                target_date = f"{today_date} (Bugün)"
        except Exception:
            pass

    return target_date, hourly_data

def send_email(target_date, data):
    sender_email = os.environ.get("MAIL_USER")
    sender_password = os.environ.get("MAIL_PASS")
    receiver_email = "selcuk.bahadir.61@gmail.com"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "EPİAS GÖP PTF Raporu - " + str(target_date)
    msg["From"] = sender_email
    msg["To"] = receiver_email

    if not data:
        html_body = "<h3>" + str(target_date) + " için EPİAŞ'tan henüz veri yayınlanmamış.</h3>"
    else:
        html_body = "<h2>" + str(target_date) + " Tarihli Gerçek PTF Raporu</h2>"
        html_body += "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
        html_body += "<tr style='background-color: #f2f2f2;'><th>Saat</th><th>PTF (TL/MWh)</th></tr>"
        for row in data:
            html_body += "<tr><td><b>" + str(row['hour']) + "</b></td><td>" + f"{row['price']:,.2f}" + " TL</td></tr>"
        html_body += "</table>"

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
    date, data = fetch_epias_ptf()
    send_email(date, data)
