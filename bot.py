import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# حافظه برای ذخیره کارها (در RAM)
user_tasks = {}

# --- ساخت منوی اصلی ---
def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ افزودن کار", callback_data="add_task"))
    markup.add(types.InlineKeyboardButton("📋 مشاهده لیست کارها", callback_data="show_list"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "سلام! به ربات «پاییز و نارنگی» خوش اومدی. از منوی زیر استفاده کن:", reply_markup=main_menu())

# --- دکمه‌ها ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    if call.data == "add_task":
        # وقتی دکمه افزودن رو می‌زنه، یک ForceReply می‌فرستیم که مستقیم جواب بده
        msg = bot.send_message(chat_id, "چه کاری قراره انجام بدیم؟ اسمش رو بنویس:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_task_addition)
    
    elif call.data == "show_list":
        send_task_list(chat_id)
        
    elif call.data.startswith("toggle_"):
        # تغییر وضعیت تیک سبز
        index = int(call.data.split("_")[1])
        user_tasks[chat_id][index]["done"] = not user_tasks[chat_id][index]["done"]
        send_task_list(chat_id, edit_mode=True, message_id=call.message.message_id)

# --- منطق افزودن کار ---
def process_task_addition(message):
    chat_id = message.chat.id
    task_text = message.text
    if chat_id not in user_tasks: user_tasks[chat_id] = []
    
    user_tasks[chat_id].append({"text": task_text, "done": False})
    bot.send_message(chat_id, f"✅ کار «{task_text}» اضافه شد!", reply_markup=main_menu())

# --- نمایش لیست شیشه‌ای ---
def send_task_list(chat_id, edit_mode=False, message_id=None):
    if chat_id not in user_tasks or not user_tasks[chat_id]:
        text = "لیست خالیه، فعلاً کاری نداریم."
    else:
        text = "کارهای لیست:"
        
    markup = types.InlineKeyboardMarkup()
    if chat_id in user_tasks:
        for i, task in enumerate(user_tasks[chat_id]):
            status = "✅" if task["done"] else "⭕"
            markup.add(types.InlineKeyboardButton(f"{status} {task['text']}", callback_data=f"toggle_{i}"))
    
    markup.add(types.InlineKeyboardButton("🔙 بازگشت به منو", callback_data="show_list")) # دکمه بازگشت

    if edit_mode:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

# --- وب‌سرور برای زنده ماندن ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run).start()
    bot.polling(none_stop=True)
