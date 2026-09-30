import os
import threading
from flask import Flask
import telebot
from telebot import types

# --- تنظیمات ---
TOKEN = "8505972442:AAHWPufVfSBxfwXpKC-UidLmjBNz7E2bwUM"
ADMIN_ID = 216989643

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# حافظه برای لیست‌ها و تسک‌ها
lists = {} # {list_id: {"title": "...", "members": [], "tasks": [{"text": "...", "status": "pending"}]}}

@app.route('/')
def home(): return "ربات در حال اجراست!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- کیبوردها ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 لیست کارهای دونفره", "➕ افزودن کار جدید", "💌 یادداشت عاشقانه")
    return markup

# --- هندلرهای تسک ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "سلام حمید عزیز، آماده‌ی مدیریت کارها هستیم! ❤️", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "➕ افزودن کار جدید")
def add_task_step1(message):
    bot.send_message(message.chat.id, "نام کار و تاریخ رو بفرست (مثلا: خرید گل - فردا ساعت ۶):")
    bot.register_next_step_handler(message, save_task)

def save_task(message):
    task_text = message.text
    # برای سادگی، فعلا توی اولین لیست کاربر اضافه می‌کنیم
    for l_id, data in lists.items():
        if message.chat.id in data["members"]:
            data["tasks"].append({"text": task_text, "status": "pending"})
            bot.send_message(message.chat.id, "✅ ثبت شد!")
            return
    bot.send_message(message.chat.id, "❌ اول باید عضو یک لیست باشی!")

@bot.message_handler(func=lambda message: message.text == "📋 لیست کارهای دونفره")
def show_tasks(message):
    for l_id, data in lists.items():
        if message.chat.id in data["members"]:
            if not data["tasks"]:
                bot.send_message(message.chat.id, "لیست خالیه!")
                return
            
            for i, task in enumerate(data["tasks"]):
                status = "✅" if task["status"] == "done" else "⏳"
                markup = types.InlineKeyboardMarkup()
                if task["status"] == "pending":
                    markup.add(types.InlineKeyboardButton("تیک زدن ✅", callback_data=f"done_{l_id}_{i}"))
                
                bot.send_message(message.chat.id, f"{status} {task['text']}", reply_markup=markup)
            return

@bot.callback_query_handler(func=lambda call: call.data.startswith("done_"))
def task_done(call):
    _, l_id, task_index = call.data.split("_")
    task = lists[l_id]["tasks"][int(task_index)]
    task["status"] = "done"
    
    # اطلاع‌رسانی به نفر دوم
    for member_id in lists[l_id]["members"]:
        if member_id != call.message.chat.id:
            bot.send_message(member_id, f"🎉 خبر خوب! کارِ «{task['text']}» توسط همسرت انجام شد.")
    
    bot.edit_message_text(f"✅ {task['text']}", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "انجام شد!")

# --- اجرای ربات ---
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()
