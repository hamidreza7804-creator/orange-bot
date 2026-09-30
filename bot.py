import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import random
import string

# --- تنظیمات اولیه ---
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- دیتابیس‌های موقت ---
pairs = {}          # {code: user_id}
connections = {}    # {user_id: group_id}
tasks_db = {}       # {group_id: [{"text": "...", "done": False}]}

# --- سرور Flask برای پایداری رندر ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

# --- دستورات ربات ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام! به ربات «پاییز و نارنگی» خوش اومدی.\n\nاز دستورات زیر استفاده کن:\n/pair - گرفتن کد برای اتصال به پارتنر\n/connect [code] - وصل شدن به پارتنر\n/add [متن کار] - اضافه کردن کار جدید\n/list - مشاهده لیست کارها")

@bot.message_handler(commands=['pair'])
def generate_pair(message):
    code = ''.join(random.choices(string.digits, k=4))
    pairs[code] = message.chat.id
    bot.reply_to(message, f"✨ کد جفت‌شدن تو اینه: `{code}`\nاین رو بفرست برای پارتنرت.")

@bot.message_handler(commands=['connect'])
def connect(message):
    try:
        code = message.text.split()[1]
        if code in pairs:
            p1 = pairs[code]
            p2 = message.chat.id
            if p1 == p2:
                bot.reply_to(message, "نمی‌تونی با خودت جفت بشی!")
                return
            group_id = f"group_{min(p1, p2)}_{max(p1, p2)}"
            connections[p1] = connections[p2] = group_id
            bot.send_message(p1, "✅ پارتنرت وصل شد! حالا می‌تونید با /add کار اضافه کنید.")
            bot.send_message(p2, "✅ تبریک! به پارتنرت وصل شدی.")
        else:
            bot.reply_to(message, "کد اشتباه یا منقضی شده.")
    except:
        bot.reply_to(message, "فرمت صحیح: /connect 1234")

@bot.message_handler(commands=['add'])
def add_task(message):
    if message.chat.id not in connections:
        bot.reply_to(message, "اول باید با پارتنرت جفت بشی! (/pair)")
        return
    text = message.text.replace('/add', '').strip()
    if not text:
        bot.reply_to(message, "متن کار رو بنویس.")
        return
    group = connections[message.chat.id]
    if group not in tasks_db: tasks_db[group] = []
    tasks_db[group].append({"text": text, "done": False})
    bot.reply_to(message, f"✨ «{text}» به لیست مشترک اضافه شد.")

@bot.message_handler(commands=['list'])
def list_tasks(message):
    if message.chat.id not in connections:
        bot.reply_to(message, "هنوز با کسی جفت نشدی!")
        return
    
    group = connections[message.chat.id]
    tasks = tasks_db.get(group, [])
    
    if not tasks:
        bot.reply_to(message, "لیست کارها خالیه!")
        return

    markup = types.InlineKeyboardMarkup()
    for i, t in enumerate(tasks):
        status = "✅" if t["done"] else "⭕"
        markup.add(types.InlineKeyboardButton(f"{status} {t['text']}", callback_data=f"toggle_{i}"))
    
    bot.send_message(message.chat.id, "📋 لیست کارهای مشترک:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def toggle_task(call):
    group = connections[call.message.chat.id]
    index = int(call.data.split("_")[1])
    tasks_db[group][index]["done"] = not tasks_db[group][index]["done"]
    
    # آپدیت لیست پس از کلیک
    tasks = tasks_db[group]
    markup = types.InlineKeyboardMarkup()
    for i, t in enumerate(tasks):
        status = "✅" if t["done"] else "⭕"
        markup.add(types.InlineKeyboardButton(f"{status} {t['text']}", callback_data=f"toggle_{i}"))
    
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

# --- اجرای ربات ---
def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    bot.infinity_polling(none_stop=True)
