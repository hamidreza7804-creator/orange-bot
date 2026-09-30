import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import random
import string
import time

# --- تنظیمات امنیتی ---
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    print("❌ خطای حیاتی: BOT_TOKEN در متغیرهای محیطی یافت نشد!")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# --- دیتابیس‌های موقت (RAM) ---
# pairs: کدهای موقت برای جفت شدن {code: user_id}
# connections: اتصالات {user_id: partner_id}
# tasks_db: لیست کارها {group_id: [{"text": "...", "done": False}]}
pairs = {}
connections = {}
tasks_db = {}

poems = [
    "پاییز یعنی نم‌نمِ باران، یعنی تو... یعنی لبخندِ نارنگی‌رنگِ تو.",
    "در دفترِ شعرم نوشتم: تمامِ جاده‌ها به قلبِ تو ختم می‌شوند.",
    "عشق یعنی همین لحظه‌ها، همین کارهای کوچک که با هم انجام می‌دهیم.",
    "تو همان بهانه‌ی زیبایی هستی که پاییز را برایم ماندگار می‌کند.",
    "برگ‌ها می‌ریزند و من با هر برگ، بیشتر عاشقت می‌شوم."
]

# --- منطق جفت شدن ---
@bot.message_handler(commands=['pair'])
def generate_pair_code(message):
    code = ''.join(random.choices(string.digits, k=4))
    pairs[code] = message.chat.id
    bot.reply_to(message, f"✨ کد جفت شدن تو اینه: `{code}`\nاین رو بفرست برای پارتنرت تا با دستور `/connect {code}` وصل بشه.", parse_mode="Markdown")

@bot.message_handler(commands=['connect'])
def connect_users(message):
    try:
        code = message.text.split()[1]
        if code in pairs:
            partner_id = pairs[code]
            if partner_id == message.chat.id:
                bot.reply_to(message, "نمی‌تونی با خودت جفت بشی!")
                return
            
            # ایجاد گروه مشترک بر اساس آیدی‌ها
            group_id = f"group_{min(message.chat.id, partner_id)}_{max(message.chat.id, partner_id)}"
            connections[message.chat.id] = group_id
            connections[partner_id] = group_id
            
            bot.send_message(message.chat.id, "✅ تبریک! حالا شما به پارتنرت متصل شدی.")
            bot.send_message(partner_id, "✅ پارتنرت بهت متصل شد! حالا می‌تونید کارهای مشترک تعریف کنید.")
        else:
            bot.reply_to(message, "کد اشتباهه یا منقضی شده.")
    except:
        bot.reply_to(message, "فرمت دستور اشتباهه. بنویس: /connect 1234")

# --- مدیریت کارها ---
@bot.message_handler(commands=['add'])
def add_task(message):
    if message.chat.id not in connections:
        bot.reply_to(message, "اول باید با پارتنرت جفت بشی. (دستور /pair)")
        return
    
    task_text = message.text.replace('/add', '').strip()
    if not task_text:
        bot.reply_to(message, "یادت رفت بنویسی چی کار داریم؟ بنویس /add [متن کار]")
        return
        
    group_id = connections[message.chat.id]
    if group_id not in tasks_db: tasks_db[group_id] = []
    tasks_db[group_id].append({"text": task_text, "done": False})
    bot.reply_to(message, f"✨ کار «{task_text}» به لیست مشترک اضافه شد.")

@bot.message_handler(commands=['list'])
def list_tasks(message):
    if message.chat.id not in connections:
        bot.reply_to(message, "هنوز با کسی جفت نشدی!")
        return
        
    show_list(message.chat.id)

def show_list(chat_id):
    group_id = connections[chat_id]
    tasks = tasks_db.get(group_id, [])
    
    if not tasks:
        bot.send_message(chat_id, "لیست کارهای مشترک خالیه. یه کار اضافه کن!")
        return

    markup = types.InlineKeyboardMarkup()
    for i, t in enumerate(tasks):
        status = "✅" if t["done"] else "⭕"
        markup.add(types.InlineKeyboardButton(f"{status} {t['text']}", callback_data=f"toggle_{i}"))
    
    bot.send_message(chat_id, "📋 لیست کارهای ما:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def toggle_task(call):
    group_id = connections[call.message.chat.id]
    index = int(call.data.split("_")[1])
    tasks_db[group_id][index]["done"] = not tasks_db[group_id][index]["done"]
    
    # ویرایش پیام کاربر
    tasks = tasks_db[group_id]
    markup = types.InlineKeyboardMarkup()
    for i, t in enumerate(tasks):
        status = "✅" if t["done"] else "⭕"
        markup.add(types.InlineKeyboardButton(f"{status} {t['text']}", callback_data=f"toggle_{i}"))
    
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

# --- شعر روزانه ---
def daily_poem_scheduler():
    while True:
        # ارسال شعر هر 24 ساعت
        time.sleep(86400)
        poem = random.choice(poems)
        for user_id in connections:
            try: bot.send_message(user_id, f"🍂 هدیه پاییزی امروز:\n\n{poem}")
            except: pass

# --- وب‌سرور ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

if __name__ == "__main__":
    Thread(target=daily_poem_scheduler, daemon=True).start()
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))).start()
    bot.polling(none_stop=True)
