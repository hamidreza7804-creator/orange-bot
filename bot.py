import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import random

# دریافت اطلاعات امنیتی از تنظیمات رندر
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID") # آیدی عددی شما
bot = telebot.TeleBot(TOKEN)

# حافظه کارهای مشترک (فعلا در RAM - ری‌استارت بشه پاک میشه)
tasks = {}

# جملات عاشقانه
romantic_responses = [
    "جان دلم؟ نارنگیِ پاییزیِ من، چی تو ذهنته؟",
    "کنارت بودن مثل نشستن زیر نور خورشیدِ یه عصر پاییزیه.",
    "من اینجا هستم، فقط برای تو. بگو چی کار کنم که لبخند بزنی؟",
    "پاییز با تو بهارِ منه. هر کاری بخوای برات انجام می‌دم.",
    "فدای اون قلب مهربونت. بگو چی تو دلته؟"
]

# --- دستورات اصلی ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام عزیز دلم! من ربات 'پاییز و نارنگی' هستم. برای اضافه کردن کارها بنویس: /add مثلا: خرید نارنگی")

@bot.message_handler(commands=['add'])
def add_task(message):
    chat_id = message.chat.id
    task_text = message.text.replace('/add', '').strip()
    if not task_text:
        bot.reply_to(message, "یادت رفت بنویسی چی کار داری؟ مثلا بنویس: /add خرید نارنگی")
        return
    
    if chat_id not in tasks: tasks[chat_id] = []
    tasks[chat_id].append({"text": task_text, "done": False})
    bot.reply_to(message, f"✨ کار «{task_text}» به لیست اضافه شد. الان می‌تونی با /list ببینیش.")

@bot.message_handler(commands=['list'])
def show_tasks(message):
    chat_id = message.chat.id
    if chat_id not in tasks or not tasks[chat_id]:
        bot.reply_to(message, "لیستت خالیه عزیزم، فعلا کاری نداریم.")
        return

    markup = types.InlineKeyboardMarkup()
    for i, task in enumerate(tasks[chat_id]):
        # ظاهر دکمه: اگر انجام شده تیک سبز، اگر نه دایره توخالی
        status = "✅" if task["done"] else "⭕"
        text = f"{status} {task['text']}"
        markup.add(types.InlineKeyboardButton(text, callback_data=f"toggle_{i}"))
    
    bot.reply_to(message, "این هم لیست کارهای امروزمون:", reply_markup=markup)

# --- سیستم تیک زدن (Callback Query) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def callback_query(call):
    chat_id = call.message.chat.id
    index = int(call.data.split("_")[1])
    
    # تغییر وضعیت تیک
    tasks[chat_id][index]["done"] = not tasks[chat_id][index]["done"]
    
    # آپدیت کردن پیام قبلی با وضعیت جدید
    markup = types.InlineKeyboardMarkup()
    for i, task in enumerate(tasks[chat_id]):
        status = "✅" if task["done"] else "⭕"
        markup.add(types.InlineKeyboardButton(f"{status} {task['text']}", callback_data=f"toggle_{i}"))
    
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)

# --- چت عاشقانه ---
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.text.startswith('/'): return
    bot.reply_to(message, random.choice(romantic_responses))

# --- بخش زنده نگه داشتن (Keep Alive) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run).start()
    bot.polling(none_stop=True)
