import time
import threading
import json
import requests
import cloudscraper
from bs4 import BeautifulSoup
from flask import Flask
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== কনফিগ ==========
BOT_TOKEN = "8707317304:AAG8f5jjLujvMrIvet1W1nO618eegkv5Miw"
CHAT_ID = "-1004437460481"
COOKIES = {
    "XSRF-TOKEN": "eyJpdiI6Iks5SkxGUjB2WTQrdkVKWDJMSzJYdXc9PSIsInZhbHVlIjoiOWtWbWhzNVFIZzJUSFd3K0d3SG1HOXVpRjNIV2wwUGxoMHlWaEE3NldDMUdMaWFRQXg4dFB3NHVHSUYxS3RDNGtSazdoNkJad2pQeEM3UzhnZEhEQzUvRUVUVjlRWDdjNkRWS3JKRGg1ZEFKK0F3dndibjNjb1hORnI3Z0FENDMiLCJtYWMiOiI4ZWJiMmVmMjBmOGViZWU2MjZjYzdkYjg2MzMwNjUwMDg1ZjdlNDlhNWMzZmEyOTU2MGFjMzQ3MjYyZjI5MzYwIiwidGFnIjoiIn0%3D",
    "_fbp": "fb.1.1787646534248.44647405065281422"
}
CHECK_INTERVAL = 5
BASE_URL = "https://www.ivasms.com"
# ===========================

app = Flask(__name__)
scraper = None
csrf_token = None
logged_in = False

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=data, timeout=10)
        if r.status_code == 200:
            logger.info("✅ টেলিগ্রামে পাঠানো হয়েছে")
        else:
            logger.error(f"❌ Telegram error: {r.text}")
    except Exception as e:
        logger.error(f"❌ error: {e}")

def login():
    global scraper, csrf_token, logged_in
    scraper = cloudscraper.create_scraper()
    scraper.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    for name, value in COOKIES.items():
        scraper.cookies.set(name, value, domain="www.ivasms.com")
    try:
        response = scraper.get(f"{BASE_URL}/portal/sms/received", timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_input = soup.find('input', {'name': '_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
                logged_in = True
                logger.info("✅ লগইন সফল!")
                return True
        logger.error(f"❌ লগইন ব্যর্থ: {response.status_code}")
        return False
    except Exception as e:
        logger.error(f"❌ লগইন error: {e}")
        return False

def get_today_sms():
    global logged_in
    if not logged_in:
        return []
    today = datetime.now().strftime("%d/%m/%Y")
    try:
        payload = {'from': today, 'to': today, '_token': csrf_token}
        headers = {
            'Accept': 'text/html, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f"{BASE_URL}/portal/sms/received"
        }
        response = scraper.post(f"{BASE_URL}/portal/sms/received/getsms", data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            sms_details = []
            items = soup.select("div.item")
            for item in items:
                try:
                    country_number = item.select_one(".col-sm-4").text.strip()
                    sms_details.append({'country_number': country_number})
                except:
                    pass
            return sms_details
        elif response.status_code == 419:
            logger.warning("⚠️ CSRF expired, re-logging...")
            logged_in = False
            login()
        return []
    except Exception as e:
        logger.error(f"❌ SMS চেক error: {e}")
        return []

def get_otp_messages(phone_range, today):
    try:
        payload = {
            '_token': csrf_token,
            'start': today,
            'end': today,
            'Range': phone_range
        }
        headers = {
            'Accept': 'text/html, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f"{BASE_URL}/portal/sms/received"
        }
        response = scraper.post(f"{BASE_URL}/portal/sms/received/getsms/number/sms", data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            messages = []
            items = soup.select(".col-9.col-sm-6 p")
            for item in items:
                msg = item.text.strip()
                if msg:
                    messages.append(f"{phone_range}|{msg}")
            return messages
        return []
    except Exception as e:
        logger.error(f"❌ OTP error: {e}")
        return []

def monitor():
    global logged_in
    logger.info("🚀 মনিটর শুরু হয়েছে...")
    if not login():
        send_telegram("❌ ivasms লগইন ব্যর্থ! Cookie আপডেট করুন।")
        return
    send_telegram("✅ <b>ivasms Bot চালু হয়েছে!</b>\nপ্রতি ৫ সেকেন্ডে চেক করবে।")
    seen = set()
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            today = datetime.now().strftime("%d/%m/%Y")
            sms_details = get_today_sms()
            for detail in sms_details:
                phone_range = detail['country_number']
                messages = get_otp_messages(phone_range, today)
                for msg in messages:
                    if msg not in seen:
                        seen.add(msg)
                        parts = msg.split("|", 1)
                        number = parts[0]
                        text = parts[1] if len(parts) > 1 else msg
                        telegram_msg = f"📩 <b>নতুন SMS!</b>\n\n<b>Number:</b> {number}\n<b>Message:</b> {text}"
                        send_telegram(telegram_msg)
            logger.info("🔄 চেক হলো")
        except Exception as e:
            logger.error(f"❌ monitor error: {e}")

@app.route('/')
def home():
    return "✅ ivasms Bot Running!"

if __name__ == "__main__":
    t = threading.Thread(target=monitor)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=10000)
