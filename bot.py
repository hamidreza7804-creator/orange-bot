import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import random
import string
import time

# دریافت توکن
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# دیتابیس‌های موقت (در حافظه رم)
pairs = {}          # {code: user_id}
connections = {}    # {user_id: group_id}
tasks_db = {}       # {group_id: [{"text": "...", "done": False}]}

# لیست اشعار
poems = [
    "پاییز یعنی نم‌نمِ باران، یعنی تو... یعنی لبخندِ نارنگی‌رنگِ تو.",
    "در دفترِ شعرم نوشتم: تمامِ جاده‌ها به قلبِ تو ختم می‌شوند.",
    "عشق یعنی همین لحظه‌ها، همین کارهای کوچک که با هم انجام می‌دهیم.",
    "تو همان بهانه‌ی زیبایی هستی که پاییز را برایم ماندگار می‌کند."
]

# --- منطق ربات ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام! به ربات «پاییز و نارنگی» خوش اومدی. برای شروع و وصل شدن به پارتنرت، از دستور /pair استفاده کن.")

@bot.message_handler(commands=['pair'])
def generate_pair(message):
    code = ''.join(random.choices(string.digits, k=4))
    pairs[code] = message.chat.id
    bot.reply_to(message, f"✨ کد جفت‌شدن تو اینه: `{code}`\nاین رو بفرست برای پارتنرت تا با دستور `/connect {code}` وصل بشه.")

@bot.message_handler(commands=['connect'])
def connect(message):
    try:
        code = message.text.split()[1]
        if code in pairs:
            p1 = pairs[code]
            p2 = message.chat.id
            if p1 == p2:
                bot.reply_to(message, "نمی‌تونی با خودت جفت بشی!")
                return
            group_id = f"group_{min(p1, p2)}_{max(p1, p2)}"
            connections[p1] = connections[p2] = group_id
            bot.send_message(p1, "✅ پارتنرت وصل شد! حالا می‌تونید با /add کار اضافه کنید.")
            bot.send_message(p2, "✅ تبریک! به پارتنرت وصل شدی.")
        else:
            bot.reply_to(message, "کد اشتباه یا منقضی شده.")
    except:
        bot.reply_to(message, "فرمت صحیح: /connect 1234")

@bot.message_handler(commands=['add'])
def add_task(message):
    if message.chat.id not in connections:
        bot.reply_to(message, "اول باید با پارتنرت جفت بشی! (/pair)")
        return
    text = message.text.replace('/add', '').strip()
    if not text:
        bot.reply_to(message, "متن کار رو بنویس.")
        return
    group = connections[message.chat.id]
    if group not in tasks_db: tasks_db[group] = []
    1 = pairs[code]
            p2 = message.chat.id
            if p1 == p2:
                bot.reply_to(message, "نمی‌تونی با خودت جفت بشی!")
                return
            group_id = f"group_{min(p1, p2)}_{max(p1, p2)}"
            connections[p1] = connections[p2] = group_id
            bot.send_message(p1, "✅ پارتنرت وصل شد! حالا می‌تونید با /add کار اضافه کنید.")
            bot.send_message(p2, "✅ تبریک! به پارتنرت وصل شدی.")
        else:
            bot.reply_to(message, "کد اشتباه یا منقضی شده.")
    except:
        bot.reply_to(message, "فرمت صحیح: /connect 1234")

@bot.message_handler(commands=['add'])
def add_task(message):
    if message.chat.id not in connections:
        bot.reply_to(message, "اول باید با پارتنرت جفت بشی! (/pair)")
        return
    text = message.text.replace('/add', '').strip()
    if not text:
        bot.reply_to(message, "متن کار رو بنویس.")
        return
    group = connections[message.chat.id]
    if group not in tasks_db: tasks_db[group] = []
    tasks_db[group].append({"text": text, "done": False})
    bot.reply_to(message, f"✨ «{text}» به لیست اضافه شد.")

@bot.message_handler(commands=['list'])
def list_tasks(message):
    if message.chat.id not in connections: return
    group = connections[message.chat.id]
    tasks = tasks_db.get(group, [])
    if not tasks این فایل را در کنار `bot.py` داشته باشید (با محتوای `pyTelegramBotAPI` و `flask`). بدون این فایل، ربات روی سرور اجرا نمی‌شود.
2.  **تنظیمات رندر:** در بخش **Environment** رندر، مطمئن شوید `BOT_TOKEN` دقیقاً درست وارد شده باشد.
3.  **دیپلوی:** بعد از ذخیره این کد در گیت‌هاب، در پنل رندر دکمه **Deploy** -> **Deploy latest commit** را بزنید و Logs را چک کنید. اگر همه چیز درست باشد، باید عبارت `TeleBot: Started polling` را در Logs ببینید.

حالا می‌توانید با خیال راحت ربات را استارت بزنید و با دستور `/pair` کار را شروع کنید! اگر خطایی دیدید، فقط متن خطای قرمز رنگِ Logs را کپی کنید تا همان لحظه رفعش کنیم.
