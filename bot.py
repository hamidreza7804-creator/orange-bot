import os
import sqlite3
import threading
from flask import Flask
import telebot

# توکن ربات تلگرام خود را اینجا قرار دهید
TOKEN = "8505972442:AAHWPufVfSBxfwXpKC-UidLmjBNz7E2bwUM"
bot = telebot.TeleBot(TOKEN)

# تنظیمات دیتابیس
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS lists (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, owner_id INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, list_id INTEGER, text TEXT, status INTEGER DEFAULT 0)")
conn.commit()

# سرور برای روشن ماندن در Render
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "سلام! ربات فعال است. برای ساخت لیست جدید دستور /new را بفرستید.")

@bot.message_handler(commands=["new"])
def new_list(message):
    msg = bot.reply_to(message, "لطفاً عنوان لیست خود را بفرستید:")
    bot.register_next_step_handler(msg, save_list)

def save_list(message):
    title = message.text
    user_id = message.from_user.id
    cursor.execute("INSERT INTO lists (title, owner_id) VALUES (?, ?)", (title, user_id))
    conn.commit()
    bot.reply_to(message, f"✅ لیست '{title}' ساخته شد!")

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.infinity_polling()
