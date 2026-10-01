import os
import telebot
from telebot import types
import random
from flask import Flask
import threading
import time

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
bot = telebot.TeleBot(TOKEN)

user_pairs = {}
tasks_db = {}
last_poem_sent = {}

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive!"

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def get_group_id(user_id):
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

INTRO_TEXT = "🍂 **به دنیای نارنجیِ ما خوش اومدی!** 🍊\n\nاینجا خونه‌ی کوچیکِ ماست، جایی که کارها رو با هم پیش می‌بریم و دلتنگی‌هامون رو با شعر پاییزی پر می‌کنیم."

@bot.message_handler(commands=['start'])
def start(message):
    try:
        # بررسی اینکه آیا کاربر از طریق لینکِ کسی اومده یا نه
        args = message.text.split()
        if len(args) > 1:
            inviter_id = int(args[1])
            if inviter_id != message.from_user.id:
                user_pairs[inviter_id] = message.from_user.id
                user_pairs[message.from_user.id] = inviter_id
                bot.send_message(message.chat.id, "💑 پارتنر تو شناسایی شد و به هم متصل شدید!")
        
        bot.send_message(message.chat.id, INTRO_TEXT, parse_mode="Markdown", reply_markup=main_menu(message.from_user.id))
    except Exception as e:
        print(f"Error in start: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try:
        user_id = call.from_user.id
        gid = get_group_id(user_id)

        if call.data == "pair_menu":
            # ساخت لینک دعوت اختصاصی
            bot_username = bot.get_me().username
            invite_link = f"https://t.me/{bot_username}?start={user_id}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔗 کپی لینک دعوت", url=invite_link))
            markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
            
            bot.edit_message_text(f"این لینک رو برای پارتنرت بفرست:\n`{invite_link}`\n\nبه محض اینکه روی لینک کلیک کنه، اتوماتیک بهت وصل می‌شه!", 
                                  call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

        elif call.data == "add_task":
            msg = bot.send_message(call.message.chat.id, "متن کار جدید رو بنویس:")
            bot.register_next_step_handler(msg, save_task)

        elif call.data == "show_tasks":
            tasks = tasks_db.get(gid, [])
            markup = types.InlineKeyboardMarkup()
            if not tasks:
                bot.answer_callback_query(call.id, "لیست خالیه!")
                return
            for i, item in enumerate(tasks):
                status = "✅" if item['done'] else "⬜️"
                markup.row(
                    types.InlineKeyboardButton(f"{status} {item['task']}", callback_data=f"toggle_{i}"),
                    types.InlineKeyboardButton("🗑", callback_data=f"delete_{i}")
                )
            markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
            bot.edit_message_text("کارهای این گروه:", call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data.startswith("toggle_"):
            idx = int(call.data.split("_")[1])
            if gid in tasks_db and idx < len(tasks_db[gid]):
                tasks_db[gid][idx]['done'] = not tasks_db[gid][idx]['done']
            handle_query(call)

        elif call.data.startswith("delete_"):
            idx = int(call.data.split("_")[1])
            if gid in tasks_db and idx < len(tasks_db[gid]):
                tasks_db[gid].pop(idx)
                bot.answer_callback_query(call.id, "کار حذف شد.")
            handle_query(call)

        elif call.data == "daily_poem":
            poem = random.choice(["پاییز یعنی عشق... 🍂", "نارنجی یعنی رنگِ ما... 🍊", "خیالِ تو... ✨"])
            last_poem_sent[user_id] = poem
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📤 ارسال برای پارتنر 💌", callback_data="send_poem"))
            markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
            bot.edit_message_text(f"🌸 {poem}", call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data == "send_poem":
            partner = user_pairs.get(user_id)
            if partner:
                bot.send_message(partner, f"عشقم برات فرستاد: {last_poem_sent.get(user_id, '...')}")
                bot.answer_callback_query(call.id, "ارسال شد! 💌")
            else:
                bot.answer_callback_query(call.id, "پارتنری وصل نیست!")

        elif call.data == "admin_panel":
            if user_id == ADMIN_ID:
                text = "🛡 وضعیت گروه‌ها:\n" + "\n".join([f"گروه {k}: {len(v)} کار" for k, v in tasks_db.items()])
                markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

        elif call.data == "back_main":
            bot.edit_message_text(INTRO_TEXT, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu(user_id))
    
    except Exception as e:
        print(f"Error in callback: {e}")

def save_task(message):
    try:
        gid = get_group_id(message.from_user.id)
        if gid not in tasks_db: tasks_db[gid] = []
        tasks_db[gid].append({"task": message.text, "done": False})
        bot.send_message(message.chat.id, "اضافه شد! 🍊")
    except Exception as e:
        print(f"Task error: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"Polling crashed: {e}")
            time.sleep(5)
