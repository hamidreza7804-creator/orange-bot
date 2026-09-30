import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import random

# تنظیم توکن از متغیرهای محیطی Render (امنیت)
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# حافظه موقت برای کارها
tasks = {}

# جملات عاشقانه و پاییزی
romantic_responses = [
    "جان دلم؟ نارنگیِ پاییزیِ من، چی تو ذهنته؟",
    "کنارت بودن مثل نشستن زیر نور خورشیدِ یه عصر پاییزیه، گرم و قشنگ.",
    "من اینجا هستم، فقط برای تو. بگو چی کار کنم که لبخند بزنی؟",
    "پاییز با تو بهارِ منه. هر کاری بخوای برات انجام می‌دم.",
    "فدای اون قلب مهربونت. بگو چی تو دلته؟"
]

# --- بخش مدیریت لیست کارها ---
@bot.message_handler(commands=['add'])
def add_task(message):
    user_id = message.chat.id
    task_text = message.text.replace('/add', '').strip()
    if not task_text:
        bot.reply_to(message, "یادت رفت بنویسی چی کار داری؟ مثلا بنویس: /add خرید نارنگی")
        return
    
    if user_id not in tasks: tasks[user_id] = []
    tasks[user_id].append({"text": task_text, "done": False})
    bot.reply_to(message, f"ثبت شد: «{task_text}». لیستت رو با /list ببین.")

@bot.message_handler(commands=['list'])
def show_tasks(message):
    user_id = message.chat.id
    if user_id not in tasks or not tasks[user_id]:
        bot.reply_to(message, "لیستت خالیه عزیزم، فعلا کاری نداریم.")
        return

    markup = types.InlineKeyboardMarkup()
    for i, task in enumerate(tasks[user_id]):
        status = "✅" if task["done"] else "⭕"
        button = types.InlineKeyboardButton(f"{status} {task['text']}", callback_data=f"toggle_{i}")
        markup.add(button)
    
    bot.reply_to(message, "این هم لیست کارهای امروزمون:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def toggle_task(call):
    index = int(call.data.split("_")[1])
    user_id = call.message.chat.id
    tasks[user_id][index]["done"] = not tasks[user_id][index]["done"]
    show_tasks(call.message) # رفرش کردن لیست

# --- بخش هوش مصنوعی عاشقانه ---
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.text.startswith('/'): return # دستورات رو کاری نداشته باش
    bot.reply_to(message, random.choice(romantic_responses))

# --- بخش زنده نگه داشتن (Keep Alive) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running, my dear!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.polling(none_stop=True)
