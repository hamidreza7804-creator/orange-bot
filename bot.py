import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import random
import datetime

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# دیتابیس‌ها
pairs = {}
connections = {}       # {user_id: group_id}
group_members = {}     # {group_id: [user1, user2]}
tasks_db = {}          # {group_id: [{"text": "...", "done": False}]}
poetry_tracker = {}    # {group_id: {"date": "...", "index": 0}}

# لیست اشعار
poems = [
    "من و تو، در میان برگ‌های پاییزی، قصه‌ای می‌سازیم که تا ابد باقیست. 🍂",
    "عشق، یعنی هم‌سفر شدن در جاده‌های سرد، با گرمای حضور تو. 🍊",
    "نارنگی‌های پاییز، طعمِ شیرینِ خنده‌های تو را می‌دهد. ✨",
    "دوست داشتن تو، ساده‌ترین اتفاق قشنگِ زندگی من است. ❤️",
    "در هیاهوی این شهر، تو آرامشِ منی، مثل یک عصرِ پاییزیِ دنج. ☕"
]

# --- توابع کمکی ---

def get_main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ افزودن کار", callback_data="ask_add_task"))
    markup.add(types.InlineKeyboardButton("📋 لیست کارهای مشترک", callback_data="show_list"))
    markup.add(types.InlineKeyboardButton("📜 شعر روزانه", callback_data="show_poem"))
    markup.add(types.InlineKeyboardButton("🔗 جفت‌شدن جدید", callback_data="start_pair"))
    return markup

def get_partner_id(user_id):
    group_id = connections.get(user_id)
    if not group_id: return None
    members = group_members.get(group_id, [])
    return members[0] if members[1] == user_id else members[1]

# --- هندلرها ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "سلام! به ربات «پاییز و نارنگی» خوش اومدی 🍂🍊\nاینجا محیط امنیه برای من و تو.\nاز دکمه‌های زیر استفاده کن:", reply_markup=get_main_menu())

# این قسمت را اضافه کن تا بتوانی کار جدید اضافه کنی
@bot.message_handler(commands=['add'])
def add_task(message):
    if message.chat.id not in connections:
        bot.reply_to(message, "⚠️ اول باید با پارتنرت جفت بشی!")
        return
        
    text = message.text.replace('/add', '').strip()
    if not text:
        bot.reply_to(message, "⚠️ لطفاً متن کار رو بعد از /add بنویس.\nمثال: `/add خرید نان`", parse_mode="Markdown")
        return
        
    group_id = connections[message.chat.id]
    if group_id not in tasks_db:
        tasks_db[group_id] = []
        
    tasks_db[group_id].append({"text": text, "done": False})
    bot.reply_to(message, "✨ به لیست اضافه شد! حالا می‌تونی در منوی اصلی با دکمه «لیست کارهای مشترک» ببینیش.")


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    
    # منوی اصلی
    if call.data == "start_pair":
        code = ''.join(random.choices("0123456789", k=4))
        pairs[code] = chat_id
        bot.edit_message_text(f"کد جفت‌شدن تو: `{code}`\nاین کد رو به پارتنرت بده تا وارد کنه.", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_menu())

    elif call.data == "show_list":
        if chat_id not in connections:
            bot.answer_callback_query(call.id, "هنوز متصل نشدی!")
            return
        
        group_id = connections[chat_id]
        tasks = tasks_db.get(group_id, [])
        markup = types.InlineKeyboardMarkup()
        for i, t in enumerate(tasks):
            status = "✅" if t["done"] else "⭕"
            markup.add(types.InlineKeyboardButton(f"{status} {t['text']}", callback_data=f"toggle_{i}"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        bot.edit_message_text("📋 لیست کارهای ما:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data == "show_poem":
        if chat_id not in connections:
            bot.answer_callback_query(call.id, "ابتدا متصل شو!")
            return
        
        group_id = connections[chat_id]
        today = str(datetime.date.today())
        
        # لاجیک شعر روزانه
        if group_id not in poetry_tracker or poetry_tracker[group_id]["date"] != today:
            poetry_tracker[group_id] = {"date": today, "index": random.randint(0, len(poems)-1)}
        
        idx = poetry_tracker[group_id]["index"]
        poem_text = poems[idx]
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💌 ارسال به پارتنر", callback_data="send_poem"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        bot.edit_message_text(f"📜 شعر امروز:\n\n{poem_text}", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data == "send_poem":
        partner = get_partner_id(chat_id)
        if partner:
            bot.send_message(partner, f"💌 پارتنرت برات یه شعر فرستاد:\n\n{poems[poetry_tracker[connections[chat_id]]['index']]}")
            bot.answer_callback_query(call.id, "شعر ارسال شد! ✨")
        else:
            bot.answer_callback_query(call.id, "کسی متصل نیست!")

    elif call.data.startswith("toggle_"):
        # لاجیک تغییر وضعیت کار (همانند قبل)
        index = int(call.data.split("_")[1])
        group_id = connections[chat_id]
        tasks_db[group_id][index]["done"] = not tasks_db[group_id][index]["done"]
        handle_callback(types.CallbackQuery(id=call.id, from_user=call.from_user, message=call.message, data="show_list"))

    elif call.data == "back_main":
        bot.edit_message_text("منوی اصلی:", chat_id, call.message.message_id, reply_markup=get_main_menu())

# --- هندلر متنی برای اتصال (چون کد باید دستی وارد شود) ---
@bot.message_handler(func=lambda message: message.text.startswith("/connect"))
def connect_via_text(message):
    code = message.text.split()[-1]
    if code in pairs:
        p1 = pairs[code]
        p2 = message.chat.id
        group_id = f"group_{p1}_{p2}"
        connections[p1] = group_id
        connections[p2] = group_id
        group_members[group_id] = [p1, p2]
        bot.send_message(p1, "✅ متصل شد!", reply_markup=get_main_menu())
        bot.send_message(p2, "✅ متصل شد!", reply_markup=get_main_menu())

# --- سرور وب (حفظ پایداری در رندر) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080))), daemon=True).start()
    bot.infinity_polling(none_stop=True)
