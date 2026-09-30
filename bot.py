import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import random
import string

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# دیتابیس‌های موقت در RAM
# pairs: کدهای جفت شدن - {code: user1_id}
# connections: اتصالات - {user_id: partner_id}
# tasks: لیست کارها - {group_id: [{"text": "...", "done": False}]}
pairs = {}
connections = {}
tasks_db = {}

# شعرها (برای ارسال روزانه)
poems = ["پاییز یعنی نم‌نمِ باران، یعنی تو...", "عشق یعنی لحظه‌های دونفره...", "پاییز با تو بهارِ منه."]

# --- دستورات جفت شدن ---
@bot.message_handler(commands=['pair'])
def generate_pair_code(message):
    code = ''.join(random.choices(string.digits, k=4))
    pairs[code] = message.chat.id
    bot.reply_to(message, f"کدِ جفت شدن تو اینه: `{code}`\nاین رو بفرست برای پارتنرت تا با دستور /connect ازش استفاده کنه.", parse_mode="Markdown")

@bot.message_handler(commands=['connect'])
def connect_users(message):
    code = message.text.split()[1] if len(message.text.split()) > 1 else None
    if code in pairs:
        partner_id = pairs[code]
        # ایجاد یک شناسه گروهی برای هر دو
        group_id = f"group_{min(message.chat.id, partner_id)}_{max(message.chat.id, partner_id)}"
        connections[message.chat.id] = group_id
        connections[partner_id] = group_id
        bot.reply_to(message, "تبریک! شما به پارتنرت متصل شدی. حالا می‌تونید کارهای مشترک تعریف کنید.")
    else:
        bot.reply_to(message, "کد اشتباهه یا منقضی شده.")

# --- مدیریت کارها ---
@bot.message_handler(commands=['add'])
def add_task(message):
    if message.chat.id not in connections:
        bot.reply_to(message, "اول باید با پارتنرت جفت بشی (دستور /pair)")
        return
    
    group_id = connections[message.chat.id]
    task_text = message.text.replace('/add', '').strip()
    
    if group_id not in tasks_db: tasks_db[group_id] = []
    tasks_db[group_id].append({"text": task_text, "done": False})
    
    bot.reply_to(message, "✅ اضافه شد! هردوتون می‌بینیدش.")

@bot.message_handler(commands=['list'])
def list_tasks(message):
    if message.chat.id not in connections:
        bot.reply_to(message, "اول باید با پارتنرت جفت بشی.")
        return
        
    group_id = connections[message.chat.id]
    tasks = tasks_db.get(group_id, [])
    
    markup = types.InlineKeyboardMarkup()
    for i, t in enumerate(tasks):
        status = "✅" if t["done"] else "⭕"
        markup.add(types.InlineKeyboardButton(f"{status} {t['text']}", callback_data=f"toggle_{i}"))
    
    bot.reply_to(message, "لیست کارهای تیم شما:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def toggle_task(call):
    group_id = connections[call.message.chat.id]
    index = int(call.data.split("_")[1])
    tasks_db[group_id][index]["done"] = not tasks_db[group_id][index]["done"]
    # (اینجا باید لیست رو رفرش کنی، مشابه کدهای قبلی)
    bot.answer_callback_query(call.id, "وضعیت تغییر کرد!")

# --- وب‌سرور ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot Active"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run).start()
    bot.polling(none_stop=True)
