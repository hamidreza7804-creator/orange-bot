import os
import telebot
from flask import Flask
from threading import Thread

# 1. خواندن توکن از محیط (Environment Variable)
TOKEN = os.environ.get('BOT_TOKEN')

if not TOKEN:
    print("خطا: BOT_TOKEN تنظیم نشده است!")
    exit()

bot = telebot.TeleBot(TOKEN)

# 2. سرور Flask برای اینکه Render سرویس را "Active" نگه دارد
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# 3. یک هندلر تست ساده برای اینکه بفهمیم ربات کار می‌کند
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! من بیدارم و آماده‌ام.")

# 4. اجرای وب‌سرور در ترد جداگانه
def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    print("در حال اجرای وب‌سرور...")
    Thread(target=run_web_server, daemon=True).start()
    
    print("در حال اجرای ربات...")
    # استفاده از infinity_polling برای جلوگیری از کرش‌های ناگهانی
    bot.infinity_polling(none_stop=True)
