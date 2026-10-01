import os
import telebot
from telebot import types
import random
from datetime import datetime
from flask import Flask
import threading

# تنظیمات اصلی
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
bot = telebot.TeleBot(TOKEN)

# دیتابیس‌های موقت
user_pairs = {} 
tasks_db = {}   
last_poem_date = {} 

# لیست اشعار (این بخش قبلاً نبود)
poems = [
    "پاییز یعنی... عشق یعنی همین که کنار همیم. 🍂",
    "نارنجی پوشیده دنیا، تو هم بپوش... که دلم می‌خواد شبیه هم باشیم. 🍊",
    "خیالِ تو، مثلِ یک لیوان چای داغ در عصرِ پاییزی... دلچسبه. ☕️",
    "دلتنگ که می‌شوم، می‌روم سراغِ همین ربات... که بدانی به یادت هستم. ✨"
]

# تابع کمکی برای گروه (این بخش قبلاً نبود)
def get_group_id(user_id):
    return user_pairs.get(user_id, user_id)

# --- بخش وب‌سرویس برای رندر (حیاتی برای جلوگیری از ارور 503) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# --- بخش ربات ---
INTRO_TEXT = "🍂 به دنیای نارنجیِ ما خوش اومدی! 🍊\n\nبرای شروع، دکمه «🔗 اتصال به پارتنر» رو بزن."

def main_menu(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 لیست کارهای مشترک 📝", callback_data="show_tasks"))
    markup.add(types.InlineKeyboardButton("➕ افزودن کار جدید 🍊", callback_data="add_task"))
    markup.add(types.InlineKeyboardButton("🌸 شعر پاییزی امروز 🍂", callback_data="daily_poem"))
    markup.add(types.InlineKeyboardButton("🔗 اتصال به پارتنر 💑", callback_data="pair_menu"))
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("🛡 پنل مدیریت", callback_data="admin_panel"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, INTRO_TEXT, reply_markup=main_menu(message.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    if call.data == "pair_menu":
        code = str(user_id)[-4:]
        bot.answer_callback_query(call.id, f"کد شما: {code}")
        bot.edit_message_text(f"کد اختصاصی تو:\n`{code}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    
    elif call.data == "daily_poem":
        poem = random.choice(poems)
        bot.edit_message_text(f"🌸 {poem}", call.message.chat.id, call.message.message_id)

# --- اجرای همزمان وب‌سرور و ربات ---
if __name__ == '__main__':
    # اجرای Flask در یک نخ (Thread) جداگانه
    threading.Thread(target=run_flask).start()
    # اجرای ربات
    bot.polling(none_stop=True)
