import requests
import time
import threading
import os
from flask import Flask
from bs4 import BeautifulSoup

# ========== কনফিগ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

COOKIES = {
    "XSRF-TOKEN": os.getenv("XSRF_TOKEN"),
    "_fbp": os.getenv("FBP")
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Referer": "https://ivasms.com/portal/live/my_sms"
}

CHECK_INTERVAL = 5
# ===========================

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ ivasms Bot Running!"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        if r.status_code == 200:
            print("✅ টেলিগ্রামে পাঠানো হয়েছে")
        else:
            print(f"❌ টেলিগ্রাম error: {r.text}")
    except Exception as e:
        print(f"❌ error: {e}")

def get_sms():
    try:
        url = "https://ivasms.com/portal/live/my_sms"
        r = requests.get(url, cookies=COOKIES, headers=HEADERS, timeout=15)

        if "login" in r.url or r.status_code == 401:
            print("⚠️ Session শেষ!")
            send_telegram("⚠️ ivasms session শেষ হয়ে গেছে! নতুন cookie দিন।")
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        messages = []
        rows = soup.select("table tbody tr")
        for row in rows:
            cols = row.find_all("td")
            # কলাম: Live SMS | SID | Paid | Limit | Message content
            if len(cols) >= 5:
                number = cols[0].get_text(strip=True)  # Live SMS (নম্বর)
                sid = cols[1].get_text(strip=True)      # SID
                content = cols[4].get_text(strip=True)  # Message content
                if number and content:
                    messages.append(f"{number}|{sid}|{content}")

        return messages
    except Exception as e:
        print(f"❌ SMS চেক error: {e}")
        return []

def monitor():
    print("🚀 ivasms মনিটর শুরু হয়েছে...")
    send_telegram("✅ <b>ivasms Bot চালু হয়েছে!</b>\nপ্রতি ৫ সেকেন্ডে চেক করবে।")

    seen = set()
    initial = get_sms()
    for msg in initial:
        seen.add(msg)
    print(f"📋 {len(seen)} টি পুরনো SMS লোড হয়েছে।")

    while True:
        time.sleep(CHECK_INTERVAL)
        current = get_sms()

        for msg in current:
            if msg not in seen:
                seen.add(msg)
                parts = msg.split("|", 2)
                number = parts[0] if len(parts) > 0 else "Unknown"
                sid = parts[1] if len(parts) > 1 else ""
                content = parts[2] if len(parts) > 2 else msg

                telegram_msg = (
                    f"📩 <b>নতুন SMS!</b>\n\n"
                    f"<b>Number:</b> {number}\n"
                    f"<b>SID:</b> {sid}\n"
                    f"<b>Message:</b> {content}"
                )
                send_telegram(telegram_msg)

        print(f"🔄 চেক হলো — {len(current)} SMS")

if __name__ == "__main__":
    t = threading.Thread(target=monitor)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=10000)
