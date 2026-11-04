import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import requests

def fetch_epias_ptf():
    # EPİAŞ'ın resmi API'si için tarih formatı (YYYY-MM-DD)
    target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # EPİAŞ Şeffaflık Platformu resmi GÖP PTF API endpoint'i
    url = f"https://seffaflik.epias.com.tr/transparency/service/market-clearing-price/ptf?startDate={target_date}&endDate={target_date}"
    
    hourly_data = []
    try:
        # EPİAŞ sistemine tarayıcı gibi görünmek için Headers ekliyoruz
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            # EPİAŞ JSON yapısındaki "items" dizisini alıyoruz
            items = result.get("body", {}).get("items", []) or result.get("items", [])
            
            for item in items:
                date_time = item.get("date", "")
                price = item.get("ptf", 0.0) # Gerçek EPİAŞ alan adı 'ptf'dir
                if price == 0.0:
                    price = item.get("price", 0.0)
                
                # Saat bilgisini ayıklama (Örn: 2026-11-06T00:00:00 -> 00:00)
                if "T" in date_time:
                    hour_str = date_time.split("T")[1][:5]
                else:
                    hour_str = str(date_time)
                    
                hourly_data.append({
                    "hour": hour_str,
                    "price": float(price)
                })
    except Exception as e:
        print(f"EPİAŞ API Bağlantı Hatası: {e}")

    return target_date, hourly_data

def send_email(target_date, data):
    sender_email = os.environ.get("MAIL_USER")
    sender_password = os.environ.get("MAIL_PASS")
    receiver_email = "selcuk.bahadir.61@gmail.com"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"⚡ Gerçek EPİAŞ GÖP PTF Raporu - {target_date}"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    if not data:
        html_content = f"<h2>⚠️ {target_date} için henüz EPİAŞ'tan veri alınamadı (Fiyatlar henüz kesinleşmemiş olabilir).</h2>"
    else:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1a73e8;">📊 {target_date} Tarihli Gerçek 24 Saatlik PTF Dağılımı</h2>
            <p>EPİAŞ Şeffaflık Platformu'ndan anlık olarak çekilen resmi Piyasa Takas Fiyatları:</p>
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
            <p style="font-size: 12px; color: #666; margin-top: 20px;">Bu rapor GitHub Actions üzerinden otomatik olarak gönderilmiştir.</p>
        </div>
        """

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Gerçek veriler e-posta ile başarıyla gönderildi.")
    except Exception as e:
        print(f"E-posta gönderilemedi: {e}")

if __name__ == "__main__":
    date, data = fetch_epias_ptf()
    send_email(date, data)
