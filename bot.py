import requests
import time
import json

# ========== কনফিগ ==========
BOT_TOKEN = "8707317304:AAG8f5jjLujvMrIvet1W1nO618eegkv5Miw"  # BotFather থেকে নতুন token নিন
CHAT_ID = "-1004437460481"

COOKIES = {
    "XSRF-TOKEN": "eyJpdiI6IlZHWW1COGxiNm04L01QdEJrMzNDWUE9PSIsInZhbHVlIjoibkNQQzdyM2E0a2Q2QzdhYzQrKzVETUtKVmt4SDExNEIxVEw1Z0xYeHg3Y1RNWk1CamUvU1d1SHYwNUpHWENQc3NrSXUrbmZpNnBPMW9MdkwzdHFxUGRmUWFnTHUyV1BNTi9SQzFiTFZ4VkVkMDZzKzd0L1hnemNybUNpSEwvRXQiLCJtYWMiOiJhMjhlMTk3ZjFmOTNkZDk5NzczYjYxYzIxZDZhYzliMTI0NDllNGM0M2MwMzNlZjA2YTBiMmJkNDY3Nzg3NWY0IiwidGFnIjoiIn0%3D",
    "_fbp": "fb.1.1787633616345.727949053228891889"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Referer": "https://ivasms.com/portal/live/my_sms"
}

CHECK_INTERVAL = 15  # সেকেন্ড
# ===========================

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
            print(f"✅ টেলিগ্রামে পাঠানো হয়েছে")
        else:
            print(f"❌ টেলিগ্রাম error: {r.text}")
    except Exception as e:
        print(f"❌ error: {e}")

def get_sms():
    try:
        url = "https://ivasms.com/portal/live/my_sms"
        r = requests.get(url, cookies=COOKIES, headers=HEADERS, timeout=15)
        
        if "login" in r.url or r.status_code == 401:
            print("⚠️ Session শেষ! নতুন cookie দরকার।")
            send_telegram("⚠️ ivasms session শেষ হয়ে গেছে! নতুন cookie দিন।")
            return []
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        
        messages = []
        rows = soup.select("table tbody tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                sender = cols[0].get_text(strip=True)
                text = cols[1].get_text(strip=True)
                if sender and text:
                    messages.append(f"{sender}|{text}")
        
        return messages
    except Exception as e:
        print(f"❌ SMS চেক error: {e}")
        return []

def main():
    print("🚀 ivasms মনিটর শুরু হয়েছে...")
    send_telegram("✅ <b>ivasms মনিটর চালু হয়েছে!</b>\nনতুন SMS আসলে এখানে পাঠানো হবে।")
    
    seen = set()
    
    # প্রথমবার পুরনো SMS লোড
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
                parts = msg.split("|", 1)
                sender = parts[0] if len(parts) > 0 else "Unknown"
                text = parts[1] if len(parts) > 1 else msg
                
                telegram_msg = f"📩 <b>নতুন SMS!</b>\n\n<b>From:</b> {sender}\n<b>Message:</b> {text}"
                send_telegram(telegram_msg)
        
        print(f"🔄 চেক হলো — {len(current)} SMS পাওয়া গেছে")

if __name__ == "__main__":
    main()
