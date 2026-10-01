import telebot
from telebot import types
import random
import os
from datetime import datetime

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
bot = telebot.TeleBot(TOKEN)

# دیتابیس‌های موقت
user_pairs = {} # {user_id: partner_id}
tasks_db = {}   # {group_id: [list_of_tasks]}
last_poem_date = {} # {group_id: date}

# متن خوش‌آمدگویی اختصاصی
INTRO_TEXT = """
🍂 **به دنیای نارنجیِ ما خوش اومدی!** 🍊

اینجا یه خونه‌ی کوچیکِ پاییزیه برای من و تو... 
من اینجام تا:
✨ لیست کارهای مشترکمون رو نظم بدم.
✨ روزانه یه شعر پاییزی بهت هدیه بدم.
✨ و کمک کنم همیشه کنار هم بمونیم.

برای شروع، دکمه «🔗 اتصال به پارتنر» رو بزن تا دنیامون یکی بشه! 🍁
"""

@bot.message_handler(commands=['start'])
def start(message):
    # این همان پیام اولی است که بعد از زدن استارت می‌بیند
    bot.send_message(message.chat.id, INTRO_TEXT, parse_mode="Markdown", reply_markup=main_menu(message.from_user.id))

def main_menu(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 لیست کارهای مشترک 📝", callback_data="show_tasks"))
    markup.add(types.InlineKeyboardButton("➕ افزودن کار جدید 🍊", callback_data="add_task"))
    markup.add(types.InlineKeyboardButton("🌸 شعر پاییزی امروز 🍂", callback_data="daily_poem"))
    markup.add(types.InlineKeyboardButton("🔗 اتصال به پارتنر 💑", callback_data="pair_menu"))
    
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("🛡 پنل مدیریت", callback_data="admin_panel"))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    
    if call.data == "pair_menu":
        code = str(user_id)[-4:] # استفاده از ۴ رقم آخر آیدی به عنوان کد اتصال
        bot.edit_message_text(f"کد اختصاصی تو برای پارتنرت اینه:\n\n`{code}`\n\nبه پارتنرت بگو این کد رو توی بخش اتصال وارد کنه. 🍊", 
                              call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data == "daily_poem":
        # منطق یک شعر در روز
        today = datetime.now().strftime("%Y-%m-%d")
        gid = get_group_id(user_id)
        
        if last_poem_date.get(gid) == today:
            bot.answer_callback_query(call.id, "امروز شعر رو دیدی! فردا دوباره بیا 🍂")
        else:
            poem = random.choice(poems)
            last_poem_date[gid] = today
            bot.edit_message_text(f"🌸 {poem}", call.message.chat.id, call.message.message_id)

    # سایر بخش‌ها همانند قبل...
