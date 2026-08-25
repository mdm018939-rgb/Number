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

# আপনার নতুন কুকি দিন:
COOKIES = {
    "cf_clearance": "9_beOIw6ORYwx.AfeJGYwZieViiOKjxQfqupTzKAl2I-1787646488-1.2.1.1-W0BnW9dbkZzmGC7vj3FJm10ezu9dZGjWS5tVI9Ymk.FFjttMxXWcBstWseZ.PaKd7DOdTlrhUaStQ0LMBxKk2n2zatBE.q9.bxr0TwlbgtqZELM38xzzlL22H32KLSNk1HDFG.nljSA79bs58NA2W0LFwtIP.YgqQQn1QK2jJs.F3k9.4P_ImnJt0RJMD5saYQC495eWpr_iCho9EF2t.2HfOVcozCxzk1qogcPFuxd869dXe8P1b1gL3J1f6O_l9Dv.SgiBr6_BH_0xOhajt6DFPHI3k3G2ZcKQdQ6d9TCaDiI0rYyZ61tpdk5ygAPsgzEkoS_CPUs7u8DLDNXTWoUqwEnr_Q.LFqR.o5ytguQgHzdNouPThp.v80eR5ygFwRgBB8TgpVgw505OIhCWeg41pppx4BSs3MkpfhLOCc8eYoRjMjFWv4eGWJ3XlAZugP6uQ9Dq9QIQp217LPY92mADpwAhp82xnSaoIOTe6smJ5W60HCDEuhG3CNvP6L7DOgwqjO9tND.OAPGn1UW5sQ",
    "_fbp": "fb.1.1787646534248.44647405065281422",
    "XSRF-TOKEN": "eyJpdiI6Im54cFNiSjhVTVlrUlhiYkh2WHZWQkE9PSIsInZhbHVlIjoiUG1hMVRMaE1PZXJhQkVxdFBqc25HK1ozNWhVeUxxM3Q5V3E1c0pHOTVDUGtldDdMa05ObDRZY2Jzd1VwTWJxTjJUZ3ZKeGRqeHMwR0dYMkRGMnhNSmRjVG10dU1TcE11bkFRS2tLWHhHUDIrellYeGtPT3oybS9wUFRkb3cvcVoiLCJtYWMiOiJkOTM1OTgxZjliN2E5MWNlZGY3ZjRjNGQ2YjQyMGZkOTIzNzI1Y2NhMDQ2Mjg2YWRmNzcxMDc0MWI4OWM2ZjE0IiwidGFnIjoiIn0%3D",
    "ivas_sms_session": "eyJpdiI6IkNvc0RuSi9mU1ZiRVVKZkZZNTYrelE9PSIsInZhbHVlIjoiVzRSSXc1VGl6RHpDSlZGQWtJaUg2QXFneFIwdWQ5NkJqYlAyc1lQNUxxSlMvbVllSkNHNFVITURkazZrZ2xtQk1zb1llM3BhVk1IMU01NTB3WGNFYWU5OHUwNnJLdmZ1NjNzNHBxK0ZxSEpjUHNRL0pDamRBTGJXMkRGcytpQ0YiLCJtYWMiOiJkZWIyMjAyZWE3ZjBkODRjZjU5NTU1MDU0ZDM1NzFiNzkwODgyM2Q4ZWU4NjBjZjUzOWU0MDgzYzNjYmJhMmVjIiwidGFnIjoiIn0%3D"
}
CHECK_INTERVAL = 5
BASE_URL = "https://www.ivasms.com"
# ===========================

app = Flask(__name__)
scraper = None
csrf_token = None
logged_in = False
login_attempts = 0
MAX_LOGIN_ATTEMPTS = 3

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
    global scraper, csrf_token, logged_in, login_attempts
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # হেডার আপডেট
        scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
        
        # Cookies সেট করুন
        for name, value in COOKIES.items():
            scraper.cookies.set(name, value, domain=".ivasms.com")
        
        # প্রথমে main page এ যান
        response = scraper.get(f"{BASE_URL}/", timeout=20)
        if response.status_code != 200:
            logger.error(f"❌ Main page error: {response.status_code}")
            return False
        
        # তারপর login page এ যান
        response = scraper.get(f"{BASE_URL}/login", timeout=20)
        if response.status_code != 200:
            logger.error(f"❌ Login page error: {response.status_code}")
            return False
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # CSRF Token খুঁজুন - বিভিন্ন ফরম্যাট চেক করুন
        csrf_input = soup.find('input', {'name': '_token'}) or soup.find('input', {'name': 'csrf-token'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
        else:
            # Meta tag এও থাকতে পারে
            meta_csrf = soup.find('meta', {'name': 'csrf-token'})
            if meta_csrf:
                csrf_token = meta_csrf.get('content')
        
        if not csrf_token:
            logger.error("❌ CSRF Token পাওয়া যায়নি!")
            return False
        
        # Login credentials (যদি ইউজারনেম/পাসওয়ার্ড লাগে)
        login_data = {
            '_token': csrf_token,
            'email': 'YOUR_EMAIL_HERE',      # আপনার ইমেইল দিন
            'password': 'YOUR_PASSWORD_HERE'  # আপনার পাসওয়ার্ড দিন
        }
        
        # লগইন রিকোয়েস্ট
        login_response = scraper.post(
            f"{BASE_URL}/login",
            data=login_data,
            headers={
                'Referer': f"{BASE_URL}/login",
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            timeout=20
        )
        
        if login_response.status_code == 200:
            # চেক করুন লগইন সফল হয়েছে কিনা
            if "dashboard" in login_response.text.lower() or "logout" in login_response.text.lower():
                logged_in = True
                login_attempts = 0
                logger.info("✅ লগইন সফল!")
                return True
            else:
                logger.error("❌ লগইন ব্যর্থ - ভুল ক্রেডেনশিয়াল")
                return False
        else:
            logger.error(f"❌ লগইন রিকোয়েস্ট ব্যর্থ: {login_response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ লগইন error: {e}")
        return False

def get_today_sms():
    global logged_in, login_attempts
    
    if not logged_in:
        return []
    
    today = datetime.now().strftime("%d/%m/%Y")
    
    try:
        # প্রথমে main page এ যান session refresh করতে
        scraper.get(f"{BASE_URL}/portal/sms/received", timeout=10)
        
        payload = {
            'from': today, 
            'to': today, 
            '_token': csrf_token
        }
        
        headers = {
            'Accept': 'text/html, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f"{BASE_URL}/portal/sms/received",
            'Origin': BASE_URL,
        }
        
        response = scraper.post(
            f"{BASE_URL}/portal/sms/received/getsms", 
            data=payload, 
            headers=headers, 
            timeout=15
        )
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            sms_details = []
            items = soup.select("div.item")
            
            for item in items:
                try:
                    number_elem = item.select_one(".col-sm-4")
                    if number_elem:
                        country_number = number_elem.text.strip()
                        sms_details.append({'country_number': country_number})
                except:
                    pass
                    
            return sms_details
            
        elif response.status_code == 419:
            logger.warning("⚠️ CSRF expired, re-logging...")
            logged_in = False
            if login_attempts < MAX_LOGIN_ATTEMPTS:
                login_attempts += 1
                login()
            return []
            
        elif response.status_code == 401 or response.status_code == 403:
            logger.warning("⚠️ Unauthorized, re-logging...")
            logged_in = False
            login()
            return []
            
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
            'Referer': f"{BASE_URL}/portal/sms/received",
            'Origin': BASE_URL,
        }
        
        response = scraper.post(
            f"{BASE_URL}/portal/sms/received/getsms/number/sms", 
            data=payload, 
            headers=headers, 
            timeout=15
        )
        
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
    send_telegram("🔄 <b>ivasms Bot চালু হচ্ছে...</b>")
    
    # লগইন চেষ্টা
    if not login():
        send_telegram("❌ ivasms লগইন ব্যর্থ! Cookie আপডেট করুন।")
        return
    
    send_telegram("✅ <b>ivasms Bot চালু হয়েছে!</b>\nপ্রতি ১০ সেকেন্ডে চেক করবে।")
    seen = set()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        
        try:
            today = datetime.now().strftime("%d/%m/%Y")
            sms_details = get_today_sms()
            
            if sms_details:
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
                            
            logger.info(f"🔄 চেক হলো - {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"❌ monitor error: {e}")
            # Error হলে পুনরায় লগইন চেষ্টা
            if not logged_in:
                login()

@app.route('/')
def home():
    return "✅ ivasms Bot Running!"

@app.route('/status')
def status():
    return f"Status: {'Logged In' if logged_in else 'Logged Out'} | CSRF: {'Set' if csrf_token else 'Not Set'}"

if __name__ == "__main__":
    t = threading.Thread(target=monitor)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=10000)
