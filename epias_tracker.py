import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import requests

def fetch_epias_ptf():
    # EPİAŞ genellikle bugünün ve yarının verilerini yayınlar
    target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # EPİAŞ Şeffaflık Platformu resmi GÖP PTF API servisi
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
            # EPİAŞ'ın güncel veri yapısını karşılama
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
                    hour_str = str(date_time)[-8: -3] if len(str(date_time)) >= 8 else "00:00"
                    
                hourly_data.append({
                    "hour": hour_str,
                    "price": float(price)
                })
    except Exception as e:
        print(f"API Bağlantı Hatası: {e}")

    # Eğer yarının fiyatı henüz EPİAŞ tarafından açıklanmadıysa (saat 17:00'den önce vb.), bugünün verisini çeker
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
    msg["Subject"] = f"⚡ EPİAŞ GÖP PTF Raporu - {target_date}"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    if not data:
        html_content = f"<h2>⚠️ {target_date} için EPİAŞ'tan henüz fiyat verisi yayınlanmamış olabilir.</h2>"
    else:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1a73e8;">📊 {target_date} Tarihli Gerçek PTF Dağılım Raporu</h2>
            <p>EPİAŞ Şeffaflık Platformu'ndan çekilen güncel saatlik fiyatlar:</p>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: left;">
                <tr style="background-color: #f2f2f2; color: #333;">
                    <th>Saat Dilimi</th>
                    <th>PTF (TL / MWh)</th>
                </tr>
        """
        for row in data:
            html_content += f"""
                <tr>
                    <td><b>{row['hour']}</b></td>
                    <td>{row['price']:,.2f} TL</td>
                </tr>
            """
        html_content += """
            </table>
            <p style="font-size: 12px; color: #666; margin-top:
