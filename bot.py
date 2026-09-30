import os
import threading
from flask import Flask
import telebot
from telebot import types

# --- تنظیمات ---
TOKEN = "8505972442:AAHM3bdUUgVZHgAP5p5JTSEOYX2jz7cRfd4"  # <--- توکن خودت
ADMIN_ID = 216989643       # <--- آیدی عددی خودت (حتما درست وارد کن)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# دیتابیس حافظه
lists = {} 
user_state = {} 

@app.route('/')
def home(): return "ربات در حال اجراست!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- منوی اصلی ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💌 یادداشت عاشقانه", "➕ افزودن کار جدید", "📋 لیست کارهای دونفره")
    # دکمه ادمین رو اضافه می‌کنیم (برای همه نشون داده می‌شه اما فقط برای ادمین کار می‌کنه)
    markup.add("⚙️ پنل مدیریت")
    return markup

# --- هندلرها ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "سلام! به ربات اختصاصی ما خوش اومدی ❤️", reply_markup=main_menu())

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.chat.id
    text = message.text

    # --- پنل مدیریت ---
    if text == "⚙️ پنل مدیریت":
        if user_id == ADMIN_ID:
            stats = f"📊 وضعیت سرور:\nتعداد لیست‌های ساخته شده: {len(lists)}\n\n(مدیریت کاربران از اینجا در دسترس است)"
            bot.send_message(user_id, stats)
        else:
            bot.send_message(user_id, "❌ دسترسی غیرمجاز!")
        return

    # --- بخش‌های اصلی ---
    if text == "💌 یادداشت عاشقانه":
        user_state[user_id] = "LOVE_NOTE"
        bot.send_message(user_id, "متن عاشقانه‌ت رو بنویس:")

    elif text == "➕ افزودن کار جدید":
        user_state[user_id] = "ADD_TASK"
        bot.send_message(user_id, "کار جدید رو بنویس:")

    elif text == "📋 لیست کارهای دونفره":
        # نمایش لیست‌ها
        found = False
        for l_id, data in lists.items():
            if user_id in data["members"]:
                bot.send_message(user_id, f"📝 لیست: {data['title']}\n" + "\n".join([t['text'] for t in data['tasks']]))
                found = True
        if not found:
            bot.send_message(user_id, "هنوز لیست کاری نداری!")

    # --- ذخیره وضعیت‌ها ---
    elif user_state.get(user_id) == "LOVE_NOTE":
        bot.send_message(user_id, "💌 یادداشت ارسال شد!")
        user_state[user_id] = None
    
    elif user_state.get(user_id) == "ADD_TASK":
        # ذخیره در حافظه
        if "default" not in lists: lists["default"] = {"title": "لیست مشترک", "members": [user_id], "tasks": []}
        lists["default"]["tasks"].append({"text": text})
        bot.send_message(user_id, "✅ کار اضافه شد!")
        user_state[user_id] = None

# اجرای ربات
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()
