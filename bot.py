import os
import telebot
from telebot import types
import random
from flask import Flask
import threading

# تنظیمات اصلی
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
bot = telebot.TeleBot(TOKEN)

# دیتابیس‌های موقت
user_pairs = {}    # {user_id: partner_id}
tasks_db = {}      # {group_id: [{"task": "text", "done": False}]}
last_poem_sent = {} # {user_id: poem_text}

# تنظیمات وب‌سرور برای جلوگیری از خواب رفتن رندر
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive!"

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# توابع کمکی
def get_group_id(user_id):
    # اگر پارتنر داشته باشد، آیدیِ مشترک، در غیر این صورت آیدیِ خودش
    return user_pairs.get(user_id, user_id)

def main_menu(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 لیست کارهای مشترک 📝", callback_data="show_tasks"))
    markup.add(types.InlineKeyboardButton("➕ افزودن کار جدید 🍊", callback_data="add_task"))
    markup.add(types.InlineKeyboardButton("🌸 شعر پاییزی امروز 🍂", callback_data="daily_poem"))
    markup.add(types.InlineKeyboardButton("🔗 اتصال به پارتنر 💑", callback_data="pair_menu"))
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("🛡 پنل مدیریت", callback_data="admin_panel"))
    return markup

# خوش‌آمدگویی
INTRO_TEXT = "🍂 **به دنیای نارنجیِ ما خوش اومدی!** 🍊\n\nاینجا خونه‌ی کوچیکِ ماست، جایی که کارها رو با هم پیش می‌بریم و دلتنگی‌هامون رو با شعر پاییزی پر می‌کنیم."

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, INTRO_TEXT, parse_mode="Markdown", reply_markup=main_menu(message.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    gid = get_group_id(user_id)

    if call.data == "pair_menu":
        code = str(user_id)[-4:]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔑 وارد کردن کد پارتنر", callback_data="enter_code"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        bot.edit_message_text(f"کد اختصاصی تو: `{code}`\n\nاین کد رو به پارتنرت بده تا وارد کنه.", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "enter_code":
        msg = bot.send_message(call.message.chat.id, "کد ۴ رقمی پارتنرت رو بنویس:")
        bot.register_next_step_handler(msg, process_pairing)

    elif call.data == "add_task":
        msg = bot.send_message(call.message.chat.id, "متن کار جدید رو بنویس:")
        bot.register_next_step_handler(msg, save_task)

    elif call.data == "show_tasks":
        tasks = tasks_db.get(gid, [])
        markup = types.InlineKeyboardMarkup()
        if not tasks:
            bot.answer_callback_query(call.id, "لیست خالیه!")
        else:
            for i, item in enumerate(tasks):
                status = "✅" if item['done'] else "⬜️"
                markup.add(types.InlineKeyboardButton(f"{status} {item['task']}", callback_data=f"toggle_{i}"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        bot.edit_message_text("لیست کارهای مشترک:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("toggle_"):
        idx = int(call.data.split("_")[1])
        tasks_db[gid][idx]['done'] = not tasks_db[gid][idx]['done']
        handle_query(call)

    elif call.data == "daily_poem":
        poem = random.choice(["پاییز یعنی عشق... 🍂", "نارنجی یعنی رنگِ ما... 🍊", "خیالِ تو، چایِ داغِ من... ☕️", "دلتنگ که می‌شوم... ✨"])
        last_poem_sent[user_id] = poem
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📤 ارسال برای پارتنر 💌", callback_data="send_poem"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        bot.edit_message_text(f"🌸 {poem}", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "send_poem":
        partner = user_pairs.get(user_id)
        if partner:
            bot.send_message(partner, f"عشقم برات فرستاد: {last_poem_sent.get(user_id, '...')}")
            bot.answer_callback_query(call.id, "شعر ارسال شد! 💌")
        else:
            bot.answer_callback_query(call.id, "پارتنری وصل نیست!")

    elif call.data == "admin_panel":
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "دسترسی نداری!")
            return
        text = "🛡 پنل مدیریت - لیست تمام کارها:\n\n"
        for g_id, tasks in tasks_db.items():
            text += f"گروه {g_id}: {len(tasks)} مورد\n"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "back_main":
        bot.edit_message_text(INTRO_TEXT, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu(user_id))

# توابع ثبت اطلاعات
def process_pairing(message):
    code = message.text
    found = None
    for uid in user_pairs.keys():
        if str(uid)[-4:] == code:
            found = uid
            break
    if found:
        user_pairs[message.from_user.id] = found
        user_pairs[found] = message.from_user.id
        bot.send_message(message.chat.id, "با موفقیت متصل شدید! 💑")
    else:
        bot.send_message(message.chat.id, "کد اشتباه بود.")

def save_task(message):
    gid = get_group_id(message.from_user.id)
    if gid not in tasks_db: tasks_db[gid] = []
    tasks_db[gid].append({"task": message.text, "done": False})
    bot.send_message(message.chat.id, "کار اضافه شد! 🍊")

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
