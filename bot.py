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

# لیست اشعار واقعی و متنوع (می‌توانی هر چقدر خواستی به این لیست اضافه کنی)
POEMS = [
    "پاییز، هزاران برگِ زرد است که در باد رقصیدند تا به من بگویند: رها کن و عاشق باش.",
    "هر برگِ پاییزی که می‌افتد، فرصتی است برای نو شدن؛ درست مثلِ ما.",
    "در هوایِ سردِ پاییز، گرمایِ دستانت تنها چیزیست که به دنیایم جان می‌دهد.",
    "نارنجیِ پاییز، رنگِ دلتنگی نیست؛ رنگِ یک شروعِ دوباره در آغوشِ توست.",
    "پاییز یعنی همین که کنارِ هم نشسته‌ایم و چای می‌نوشیم، باقی همه بهانه‌ست.",
    "باز پاییز است و من به تو فکر می‌کنم، میانِ همهمه‌یِ برگ‌هایِ خشکِ زیرِ پا.",
    "عشق، همانِ حالِ خوشی است که در غروبِ سردِ پاییز، گرمایِ نگاهت به من می‌بخشد.",
    "پاییز زیباترین بهانه‌یِ خداست تا به ما یادآوری کند که تغییر، چه شکوهی دارد.",
    "در ازدحامِ رنگ‌هایِ پاییزی، فقط تویی که در چشم‌هایم سبز می‌مانی.",
    "عاشقانه هایمان مثلِ چایِ داغِ پاییزی، جان‌بخش و ماندگار است."
]

user_pairs = {}
tasks_db = {}
last_poem_sent = {}

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive!"

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def get_group_id(user_id):
    if user_id in user_pairs:
        return min(user_id, user_pairs[user_id])
    return user_id

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
    args = message.text.split()
    if len(args) > 1:
        inviter_id = int(args[1])
        if inviter_id != message.from_user.id:
            user_pairs[inviter_id] = message.from_user.id
            user_pairs[message.from_user.id] = inviter_id
            bot.send_message(message.chat.id, "💑 اتصال موفقیت‌آمیز! لیست کارهای شما مشترک شد.")
    
    bot.send_message(message.chat.id, "🍂 **به دنیای نارنجیِ ما خوش اومدی، اینجا خونه‌ی کوچیکِ ماست، جایی که کارها رو با هم پیش می‌بریم!** 🍊", parse_mode="Markdown", reply_markup=main_menu(message.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    gid = get_group_id(user_id)

    if call.data == "pair_menu":
        bot_username = bot.get_me().username
        invite_link = f"https://t.me/{bot_username}?start={user_id}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📤 اشتراک‌گذاری لینک", switch_inline_query=f"بیا با هم کارهامون رو مدیریت کنیم: {invite_link}"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        bot.edit_message_text("لینک دعوت رو برای پارتنرت بفرست:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "add_task":
        msg = bot.send_message(call.message.chat.id, "متن کار جدید رو بنویس:")
        bot.register_next_step_handler(msg, save_task)

    elif call.data == "show_tasks":
        tasks = tasks_db.get(gid, [])
        markup = types.InlineKeyboardMarkup()
        
        if not tasks:
            bot.answer_callback_query(call.id, "لیست خالیه!")
            return

        # ساخت متن بدنه
        task_body = "📌 **لیست کارهای ما:**\n\n"
        for i, item in enumerate(tasks):
            task_body += f"{i+1}. {item['task']}\n"
            
            # افزودن دکمه‌های کنترلی برای هر کار
            p1_mark = "✅" if item['p1_done'] else "⬜"
            p2_mark = "✅" if item['p2_done'] else "⬜"
            
            markup.row(
                types.InlineKeyboardButton(f"من: {p1_mark}", callback_data=f"t1_{i}"),
                types.InlineKeyboardButton(f"پارتنر: {p2_mark}", callback_data=f"t2_{i}"),
                types.InlineKeyboardButton("🗑", callback_data=f"del_{i}")
            )

        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        bot.edit_message_text(task_body, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data.startswith("t1_") or call.data.startswith("t2_"):
        parts = call.data.split("_")
        idx = int(parts[1])
        if gid in tasks_db and idx < len(tasks_db[gid]):
            if parts[0] == "t1": tasks_db[gid][idx]['p1_done'] = not tasks_db[gid][idx]['p1_done']
            else: tasks_db[gid][idx]['p2_done'] = not tasks_db[gid][idx]['p2_done']
            call.data = "show_tasks"
            handle_query(call)

    elif call.data.startswith("del_"):
        idx = int(call.data.split("_")[1])
        if gid in tasks_db and idx < len(tasks_db[gid]):
            tasks_db[gid].pop(idx)
        call.data = "show_tasks"
        handle_query(call)

    elif call.data == "daily_poem":
        poem = random.choice(POEMS)
        last_poem_sent[user_id] = poem
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📤 ارسال برای پارتنر 💌", callback_data="send_poem"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        bot.edit_message_text(f"🌸 {poem}", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "send_poem":
        partner = user_pairs.get(user_id)
        if partner:
            bot.send_message(partner, f"💌 عشقت برات فرستاد:\n\n{last_poem_sent.get(user_id, '...')}")
            bot.answer_callback_query(call.id, "با موفقیت ارسال شد! 💌")
        else:
            bot.answer_callback_query(call.id, "پارتنری وصل نیست!")

    elif call.data == "back_main":
        bot.edit_message_text("🍂 **به دنیای نارنجیِ ما خوش اومدی!** 🍊", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu(user_id))

def save_task(message):
    gid = get_group_id(message.from_user.id)
    if gid not in tasks_db: tasks_db[gid] = []
    tasks_db[gid].append({"task": message.text, "p1_done": False, "p2_done": False})
    bot.send_message(message.chat.id, "اضافه شد! 🍊")

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            time.sleep(5)
