import os
import json
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = 32245412
API_HASH = "2fa7397a6659ef9750a3adac3ea7dffe"
BOT_TOKEN = "8711416626:AAHYkD98HDlzN1X3O58zQVqtV14oYb_DcZs"
ADMIN_IDS = [6625019627, 8216971392]
ALLOWED_USERS = []

app = Client("mt_number_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DB_FILE = "stock_db.json"

def load_db():
    default = {"Towhid": [], "Mamun": [], "Allowed": []}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                for k in default:
                    if k not in data: data[k] = default[k]
                return data
        except: return default
    return default

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

stocks = load_db()
admin_state = {}

def is_allowed(user_id):
    return user_id in ADMIN_IDS or user_id in ALLOWED_USERS or user_id in stocks.get("Allowed", [])

async def send_denied(message):
    uid = message.from_user.id
    text = (f"🚫 **অ্যাক্সেস ডিনাইড!**\nআপনার আইডি: `{uid}`\n\n"
            f"আপনার এই বট ব্যবহারের অনুমতি নেই। অনুমতির জন্য অ্যাডমিনের সাথে যোগাযোগ করুন।")
    btns = InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url="https://t.me/mrincome9")]])
    await message.reply_text(text, reply_markup=btns)

@app.on_message(filters.command(["start", "get", "add", "clear", "allow", "ban", "help"]))
async def gatekeeper(client, message):
    if not is_allowed(message.from_user.id):
        await send_denied(message)
        return
    message.continue_propagation()

@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    txt = (
        "🛠 **COMMAND CENTER**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔹 /start - বট শুরু করতে\n"
        "🔹 /get - নম্বর নিতে\n"
        "🔹 /help - এই মেনু দেখতে\n\n"
        "👑 **Admin Only:**\n"
        "🔹 /add - স্টকে নম্বর যোগ করতে\n"
        "🔹 /clear - স্টক ডিলিট করতে\n"
        "🔹 /allow (ID) - ইউজার অ্যাড করতে\n"
        "🔹 /ban (ID) - ইউজার মুছতে\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    await message.reply_text(txt)

@app.on_message(filters.command("start"))
async def start(client, message):
    btns = InlineKeyboardMarkup([[InlineKeyboardButton("📥 Get Numbers", callback_data="back_home")]])
    await message.reply_text(
        "💎 **MT NUMBER PREMIUM**\n"
        "───────────────────\n"
        "স্বাগতম! নম্বর নিতে বাটন চাপুন।",
        reply_markup=btns
    )

@app.on_message(filters.command("get"))
async def get_cmd(client, message):
    t, m = len(stocks["Towhid"]), len(stocks["Mamun"])
    btns = InlineKeyboardMarkup([[
        InlineKeyboardButton(f"👤 Towhid [{t}]", callback_data="deliver_Towhid"),
        InlineKeyboardButton(f"👤 Mamun [{m}]", callback_data="deliver_Mamun")
    ]])
    await message.reply_text("👤 **কার স্টক থেকে নম্বর নিতে চান?**", reply_markup=btns)

@app.on_message(filters.command("allow"))
async def allow_cmd(client, message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply_text("❌ **তুমি Admin না!**\nএই কমান্ড ব্যবহারের অনুমতি নেই।")
        return
    if len(message.command) < 2:
        await message.reply_text("⚠️ নিয়ম: `/allow USER_ID` লিখুন।")
        return
    try:
        uid = int(message.command[1])
        if uid not in stocks["Allowed"]:
            stocks["Allowed"].append(uid)
            save_db(stocks)
            await message.reply_text(f"✅ ইউজার `{uid}` অনুমোদিত হয়েছে।")
            try:
                await client.send_message(
                    uid,
                    "✅ **আপনাকে এক্সেস দেওয়া হয়েছে!**\n\n"
                    "এখন আপনি বট ব্যবহার করতে পারবেন।\n"
                    "শুরু করতে /start দিন। 😊"
                )
            except:
                pass
        else:
            await message.reply_text(f"⚠️ ইউজার `{uid}` আগেই অনুমোদিত আছে।")
    except:
        await message.reply_text("❌ আইডিটি সঠিক নয়।")

@app.on_message(filters.command("ban"))
async def ban_cmd(client, message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply_text("❌ **তুমি Admin না!**\nএই কমান্ড ব্যবহারের অনুমতি নেই।")
        return
    if len(message.command) < 2:
        return
    try:
        uid = int(message.command[1])
        if uid in stocks["Allowed"]:
            stocks["Allowed"].remove(uid)
            save_db(stocks)
            await message.reply_text(f"🚫 ইউজার `{uid}` ব্যান হয়েছে।")
            try:
                await client.send_message(
                    uid,
                    "🚫 **আপনাকে ব্যান করা হয়েছে!**\n\n"
                    "আপনার বট ব্যবহারের অনুমতি বাতিল করা হয়েছে।\n"
                    "বিস্তারিত জানতে অ্যাডমিনের সাথে যোগাযোগ করুন।"
                )
            except:
                pass
        else:
            await message.reply_text(f"⚠️ ইউজার `{uid}` allowed লিস্টে নেই।")
    except:
        pass

async def deliver_numbers(client, callback_query, name):
    if not stocks[name]:
        await callback_query.answer(f"⚠️ {name} এর স্টক খালি!", show_alert=True)
        return

    delivery = stocks[name][:10]
    stocks[name] = stocks[name][10:]
    save_db(stocks)

    txt = "\n".join([f"`{n}`" for n in delivery])
    msg_text = (
        f"📱 **YOUR NUMBERS ({name})**\n"
        f"━━━━━━━━━━━━━━\n"
        f"{txt}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📦 বাকি স্টক: {len(stocks[name])} টি"
    )

    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 আরও ১০টি নিন", callback_data=f"deliver_{name}")],
        [InlineKeyboardButton("🔙 মেনু", callback_data="back_home")]
    ])

    try: await callback_query.message.delete()
    except: pass

    sent = await callback_query.message.reply_text(msg_text, reply_markup=btns)

    # ৭ মিনিট পর অটো ডিলিট
    await asyncio.sleep(420)
    try:
        await sent.delete()
    except:
        pass

@app.on_callback_query()
async def cb_handler(client, query):
    if not is_allowed(query.from_user.id): return
    data = query.data

    if data.startswith("deliver_"):
        await deliver_numbers(client, query, data.split("_")[1])
    elif data.startswith("add_"):
        admin_state[query.from_user.id] = data.split("_")[1]
        await query.message.edit_text(f"📝 **{data.split('_')[1]}** এর জন্য নম্বর পাঠান:")
    elif data.startswith("confirm_clear_"):
        n = data.split("_")[2]
        stocks[n] = []
        save_db(stocks)
        await query.message.edit_text(f"✅ **{n}** এর স্টক ক্লিয়ার হয়েছে।")
    elif data == "back_home":
        t, m = len(stocks["Towhid"]), len(stocks["Mamun"])
        btns = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"👤 Towhid [{t}]", callback_data="deliver_Towhid"),
            InlineKeyboardButton(f"👤 Mamun [{m}]", callback_data="deliver_Mamun")
        ]])
        await query.message.edit_text("👤 **কার স্টক থেকে নম্বর নিতে চান?**", reply_markup=btns)

@app.on_message(filters.command("add"))
async def add_cmd(client, message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply_text("❌ **তুমি Admin না!**\nএই কমান্ড ব্যবহারের অনুমতি নেই।")
        return
    btns = InlineKeyboardMarkup([[
        InlineKeyboardButton("👤 Towhid", callback_data="add_Towhid"),
        InlineKeyboardButton("👤 Mamun", callback_data="add_Mamun")
    ]])
    await message.reply_text("📂 **NUMBER ADD PANEL**", reply_markup=btns)

@app.on_message(filters.command("clear"))
async def clear_cmd(client, message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply_text("❌ **তুমি Admin না!**\nএই কমান্ড ব্যবহারের অনুমতি নেই।")
        return
    btns = InlineKeyboardMarkup([[
        InlineKeyboardButton("👤 Towhid", callback_data="confirm_clear_Towhid"),
        InlineKeyboardButton("👤 Mamun", callback_data="confirm_clear_Mamun")
    ]])
    await message.reply_text("🗑 **কার স্টক ডিলিট করতে চান?**", reply_markup=btns)

@app.on_message(filters.text & filters.user(ADMIN_IDS))
async def saving_process(client, message):
    uid = message.from_user.id
    if uid in admin_state:
        name = admin_state[uid]
        nums = message.text.strip().split("\n")
        stocks[name].extend(nums)
        save_db(stocks)
        del admin_state[uid]
        btns = InlineKeyboardMarkup([[InlineKeyboardButton("📱 নম্বর নিন", callback_data="back_home")]])
        await message.reply_text(f"✅ {len(nums)} টি নম্বর যোগ হয়েছে।", reply_markup=btns)
        try: await message.delete()
        except: pass

app.run()