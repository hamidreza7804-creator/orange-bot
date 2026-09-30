import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import random

# خواندن توکن و آیدی مدیر از صندوق امن رندر (Environment Variables)
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

bot = telebot.TeleBot(TOKEN)

# حافظه موقت برای لیست کارها
tasks = {}

# پاسخ‌های عاشقانه و پاییزی
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
        bot.reply_to(message, "یادت رفت بنویسی چی کار داری؟ مثلا بنویس:\n`/add خرید نارنگی`")
        return
    
    if user_id not in tasks: 
        tasks[user_id] = []
    tasks[user_id].append({"text": task_text, "done": False})
    bot.reply_to(message, f"ثبت شد: «{task_text}». لیستت رو با دستور /list ببین.")

@bot.message_handler(commands=['list'])
def show_tasks(message):
    user_id = message.chat.id
    if user_id not in tasks or not tasks[user_id]:
        bot.reply_to(message, "لیستت خالیه عزیزم، فعلا کاری نداریم. با /add کار جدید اضافه کن.")
        return

    markup = types.InlineKeyboardMarkup()
    for i, task in enumerate(tasks[user_id]):
        status = "✅" if task["done"] else "⭕"
        button = types.InlineKeyboardButton(f"{status} {task['text']}", callback_data=f"toggle_{i}")
        markup.add(button)
    
    bot.reply_to(message, "اینم لیست کارهای امروزمون (برای تیک زدن رویشان بزن):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def toggle_task(call):
    try:
        index = int(call.data.split("_")[1])
        user_id = call.message.chat.id
        if user_id in tasks and len(tasks[user_id]) > index:
            tasks[user_id][index]["done"] = not tasks[user_id][index]["done"]
            
            # به‌روزرسانی دکمه‌ها
            markup = types.InlineKeyboardMarkup()
            for i, task in enumerate(tasks[user_id]):
                status = "✅" if task["done"] else "⭕"
                button = types.InlineKeyboardButton(f"{status} {task['text']}", callback_data=f"toggle_{i}")
                markup.add(button)
            
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

# --- بخش پنل مدیریت اختصاصی ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "⚙️ **پنل مدیریت ربات پاییز و نارنگی**\n\nوضعیت سرور: فعال و پایدار 🟢\nهمه چیز تحت کنترله قربان!")
    else:
        bot.reply_to(message, "شما اجازه دسترسی به این بخش رو ندارید.")

# --- بخش گفتگو و هوش عاشقانه ---
@bot.message_handler(func=lambda message: True)
def chat_with_bot(message):
    if message.text.startswith('/'): 
        return
    bot.reply_to(message, random.choice(romantic_responses))

# --- بخش زنده نگه داشتن سرور در رندر (Keep-Alive) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    # اجرای وب‌سرور در پس‌زمینه برای نخوابیدن رندر
    t = Thread(target=run_flask)
    t.start()
    
    # اجرای ربات تلگرام
    bot.infinity_polling(skip_pending=True)
