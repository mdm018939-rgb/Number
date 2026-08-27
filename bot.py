import time
import threading
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
    "_fbp": "fb.1.1787846359150.208365323434881442",
    "cf_chl_rc_ni": "2",
    "XSRF-TOKEN": "eyJpdiI6Im1RUzNHSm11MXF4bXRkaDRXTVRjT2c9PSIsInZhbHVlIjoiV0JvTktLaTJTSUlOc3JsUk45blRBRG85QzBmYktpaDArOTJZYjBKNkFQNWYxNmZhTWk1VTJuY0tyZ1RlNG45YzV6ZmVxSTlzM3h1SXZFd0k3YXZUYTJjTzlBRVgybkpvQWVkUlo0SkpUdTgvbzZraTdoSXhjeE9Vc1FzUUZXdlQiLCJtYWMiOiI1ODQ3MmZjMWQ3NTViZWVjNjlkYjhlMzE3M2M4YjU0YjllNDZlMzBhNjliNTA3ODNkNjE0ZWQyNDAzNDEwNzY4IiwidGFnIjoiIn0%3D"
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
        response = scraper.get(f"{BASE_URL}/portal/live/my_sms", timeout=15)

        logger.info(f"Login response: {response.status_code}")
        logger.info(f"Final URL: {response.url}")
        logger.info(f"Response start: {response.text[:1000]}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            csrf_input = soup.find('input', {'name': '_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
                logged_in = True
                logger.info("✅ লগইন সফল!")
                return True

            meta = soup.find('meta', {'name': 'csrf-token'})
            if meta:
                csrf_token = meta.get('content')
                logged_in = True
                logger.info("✅ লগইন সফল (meta)!")
                return True

        logger.error(f"❌ লগইন ব্যর্থ: {response.status_code}")
        logger.error(f"Response: {response.text[:500]}")
        return False

    except Exception as e:
        logger.error(f"❌ লগইন error: {e}")
        return False

def get_sms():
    global logged_in
    if not logged_in:
        return []
    try:
        headers = {
            'Accept': 'text/html, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f"{BASE_URL}/portal/live/my_sms"
        }
        response = scraper.get(f"{BASE_URL}/portal/live/my_sms", headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            messages = []
            rows = soup.select("table tbody tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    number = cols[0].get_text(strip=True)
                    content = cols[-1].get_text(strip=True)
                    if number and content:
                        messages.append(f"{number}|{content}")
            return messages
        elif response.status_code == 302 or "login" in response.url:
            logger.warning("⚠️ Session শেষ!")
            logged_in = False
            send_telegram("⚠️ Cookie শেষ! নতুন cookie দিন।")
        return []
    except Exception as e:
        logger.error(f"❌ SMS চেক error: {e}")
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
            current = get_sms()
            for msg in current:
                if msg not in seen:
                    seen.add(msg)
                    parts = msg.split("|", 1)
                    number = parts[0]
                    text = parts[1] if len(parts) > 1 else msg
                    telegram_msg = f"📩 <b>নতুন SMS!</b>\n\n<b>Number:</b> {number}\n<b>Message:</b> {text}"
                    send_telegram(telegram_msg)
            logger.info(f"🔄 চেক হলো — {len(current)} SMS")
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