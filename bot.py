import os
import threading
from flask import Flask
import telebot
from telebot import types

# راه‌اندازی سرور وب کوچک برای زنده نگه داشتن در Render
app = Flask(__name__)

@app.route('/')
def home():
    return "ربات برنامه‌ریزی مشترک فعال و آنلاین است!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# توکن ربات شما
TOKEN = "8505972442:AAHWPufVfSBxfwXpKC-UidLmjBNz7E2bwUM"  # توکن اختصاصی ربات
bot = telebot.TeleBot(TOKEN)

# دیتابیس ساده در حافظه
# ساختار:
# lists = { list_id: { "title": "نام لیست", "owner": user_id, "members": [user_id1, ...], "tasks": [{"id": 1, "text": "متن", "done": False}] } }
lists = {}
user_active_list = {}  # user_id: active_list_id
user_state = {}        # وضعیت فعلی کاربر برای دریافت ورودی

# کیبورد اصلی ربات
def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_my_lists = types.KeyboardButton("📋 لیست‌های من")
    btn_new_list = types.KeyboardButton("➕ ایجاد لیست جدید")
    btn_join_list = types.KeyboardButton("🔗 پیوستن به لیست دوستان")
    btn_help = types.KeyboardButton("راهنما ❓")
    markup.add(btn_my_lists, btn_new_list, btn_join_list, btn_help)
    return markup

# نمایش آیتم‌های یک لیست با دکمه‌های شیشه‌ای
def get_list_markup(list_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    task_list = lists.get(list_id, {}).get("tasks", [])
    
    for task in task_list:
        status_icon = "✅" if task["done"] else "⭕️"
        text = f"{status_icon} {task['text']}"
        markup.add(
            types.InlineKeyboardButton(text, callback_data=f"toggle_{list_id}_{task['id']}"),
            types.InlineKeyboardButton("🗑 حذف", callback_data=f"del_{list_id}_{task['id']}")
        )
    
    markup.add(
        types.InlineKeyboardButton("➕ افزودن کار جدید", callback_data=f"addtask_{list_id}"),
        types.InlineKeyboardButton("👥 اعضا و کد دعوت", callback_data=f"share_{list_id}")
    )
    markup.add(types.InlineKeyboardButton("🔙 بازگشت به لیست‌ها", callback_data="back_to_lists"))
    return markup

# پیام /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_name = message.from_user.first_name or "کاربر عزیز"
    
    # بررسی آیا کاربر از طریق لینک دعوت آمده است
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("join_"):
        list_id = args[1].replace("join_", "")
        if list_id in lists:
            if user_id not in lists[list_id]["members"]:
                lists[list_id]["members"].append(user_id)
                bot.send_message(user_id, f"🎉 شما با موفقیت به لیست «{lists[list_id]['title']}» اضافه شدید!", reply_markup=main_menu_keyboard())
                # اطلاع به بقیه اعضا
                notify_members(list_id, f"👤 {user_name} به لیست «{lists[list_id]['title']}» پیوست.", exclude_user=user_id)
            else:
                bot.send_message(user_id, f"شما قبلاً در لیست «{lists[list_id]['title']}» عضو بودید.", reply_markup=main_menu_keyboard())
            show_list(user_id, list_id)
            return

    welcome_text = (
        f"سلام {user_name} عزیز! خوش اومدی 🧡\n\n"
        "این ربات مخصوص **برنامه‌ریزی و لیست کارهای مشترک** با دوستان، خانواده و همکارانته.\n\n"
        "یکی از گزینه‌های زیر رو انتخاب کن:"
    )
    bot.send_message(user_id, welcome_text, reply_markup=main_menu_keyboard())

# هندلر پیام‌های متنی
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.chat.id
    text = message.text

    # حالت‌های چندمرحله‌ای
    state = user_state.get(user_id)

    if state == "WAITING_FOR_LIST_NAME":
        list_id = f"L{len(lists) + 1001}"
        lists[list_id] = {
            "title": text,
            "owner": user_id,
            "members": [user_id],
            "tasks": []
        }
        user_state[user_id] = None
        bot.send_message(user_id, f"✅ لیست «{text}» با موفقیت ساخته شد!", reply_markup=main_menu_keyboard())
        show_list(user_id, list_id)
        return

    elif state == "WAITING_FOR_JOIN_CODE":
        list_id = text.strip()
        user_state[user_id] = None
        if list_id in lists:
            if user_id not in lists[list_id]["members"]:
                lists[list_id]["members"].append(user_id)
                bot.send_message(user_id, f"🎉 شما به لیست «{lists[list_id]['title']}» ملحق شدید!", reply_markup=main_menu_keyboard())
                notify_members(list_id, f"👤 یکی از دوستان به لیست «{lists[list_id]['title']}» اضافه شد.", exclude_user=user_id)
            show_list(user_id, list_id)
        else:
            bot.send_message(user_id, "❌ کد نامعتبر است! لطفاً مجدد امتحان کنید.", reply_markup=main_menu_keyboard())
        return

    elif state and state.startswith("WAITING_FOR_TASK_"):
        list_id = state.replace("WAITING_FOR_TASK_", "")
        if list_id in lists:
            new_task_id = len(lists[list_id]["tasks"]) + 1
            lists[list_id]["tasks"].append({"id": new_task_id, "text": text, "done": False})
            user_state[user_id] = None
            bot.send_message(user_id, f"✅ مورد جدید اضافه شد:\n«{text}»")
            notify_members(list_id, f"📝 مورد جدید به لیست «{lists[list_id]['title']}» اضافه شد:\n«{text}»", exclude_user=user_id)
            show_list(user_id, list_id)
        return

    # منوهای کیبورد اصلی
    if text == "➕ ایجاد لیست جدید":
        user_state[user_id] = "WAITING_FOR_LIST_NAME"
        bot.send_message(user_id, "لطفاً **نام یا عنوان لیست** رو بفرست:\n(مثلاً: خریدهای خانه، کارهای پروژه، برنامه سفر...)")

    elif text == "📋 لیست‌های من":
        user_lists = [l_id for l_id, data in lists.items() if user_id in data["members"]]
        if not user_lists:
            bot.send_message(user_id, "شما هنوز هیچ لیستی ندارید! با دکمه «➕ ایجاد لیست جدید» یکی بسازید.")
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for l_id in user_lists:
                markup.add(types.InlineKeyboardButton(f"📁 {lists[l_id]['title']}", callback_data=f"view_{l_id}"))
            bot.send_message(user_id, "👇 یکی از لیست‌های خود را انتخاب کنید:", reply_markup=markup)

    elif text == "🔗 پیوستن به لیست دوستان":
        user_state[user_id] = "WAITING_FOR_JOIN_CODE"
        bot.send_message(user_id, "🔑 لطفاً **کد اختصاصی لیست** که دوستت برات فرستاده رو وارد کن:")

    elif text == "راهنما ❓":
        help_text = (
            "📌 **راهنمای استفاده از ربات:**\n\n"
            "۱. با زدن «ایجاد لیست جدید» یک پوشه مشترک برای کارها بسازید.\n"
            "۲. وارد لیست شوید و با دکمه «اعضا و کد دعوت»، لینک یا کد را برای دوستانتان بفرستید.\n"
            "۳. هر کسی کاری انجام داد روی آیکون دایره ⭕️ بزند تا تیک سبز ✅ بخورد.\n"
            "۴. تغییرات به‌صورت آنی برای تمام اعضا هماهنگ می‌شود."
        )
        bot.send_message(user_id, help_text)

# نمایش یک لیست مشخص
def show_list(user_id, list_id):
    if list_id not in lists:
        bot.send_message(user_id, "❌ این لیست پیدا نشد!")
        return
    data = lists[list_id]
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    msg = f"📋 **{data['title']}**\n\nتعداد کارها: {total} | انجام شده: {done_count} ✅\nبرای تغییر وضعیت، روی هر مورد کلیک کنید:"
    bot.send_message(user_id, msg, parse_mode="Markdown", reply_markup=get_list_markup(list_id))

# هندلر کلیک روی دکمه‌های شیشه‌ای
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    data = call.data

    if data.startswith("view_"):
        list_id = data.replace("view_", "")
        show_list(user_id, list_id)

    elif data.startswith("toggle_"):
        _, list_id, task_id = data.split("_")
        task_id = int(task_id)
        if list_id in lists:
            for t in lists[list_id]["tasks"]:
                if t["id"] == task_id:
                    t["done"] = not t["done"]
                    status_text = "انجام شد ✅" if t["done"] else "به حالت انجام‌نشده برگشت ⭕️"
                    notify_members(list_id, f"🔔 مورد «{t['text']}» در لیست «{lists[list_id]['title']}» {status_text}.", exclude_user=user_id)
                    break
            bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=get_list_markup(list_id))

    elif data.startswith("del_"):
        _, list_id, task_id = data.split("_")
        task_id = int(task_id)
        if list_id in lists:
            lists[list_id]["tasks"] = [t for t in lists[list_id]["tasks"] if t["id"] != task_id]
            bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=get_list_markup(list_id))
            bot.answer_callback_query(call.id, "مورد حذف شد.")

    elif data.startswith("addtask_"):
        list_id = data.replace("addtask_", "")
        user_state[user_id] = f"WAITING_FOR_TASK_{list_id}"
        bot.send_message(user_id, "✍️ متن کار یا موردی که می‌خواهی اضافه کنی را بنویس:")

    elif data.startswith("share_"):
        list_id = data.replace("share_", "")
        if list_id in lists:
            share_text = (
                f"🤝 دعوت به لیست مشترک: **{lists[list_id]['title']}**\n\n"
                f"🔑 کد دعوت اختصاصی: `{list_id}`\n\n"
                f"🔗 یا کلیک روی لینک مستقیم ورود:\n"
                f"https://t.me/Orang17e_bot?start=join_{list_id}"
            )
            bot.send_message(user_id, share_text, parse_mode="Markdown")

    elif data == "back_to_lists":
        bot.delete_message(user_id, call.message.message_id)
        handle_messages(call.message)

    bot.answer_callback_query(call.id)

# تابع اطلاع‌رسانی به همه اعضای لیست
def notify_members(list_id, text, exclude_user=None):
    if list_id in lists:
        for member_id in lists[list_id]["members"]:
            if member_id != exclude_user:
                try:
                    bot.send_message(member_id, text)
                except Exception:
                    pass

# اجرای همزمان وب‌سرور و ربات
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("ربات با موفقیت راه‌اندازی شد...")
    bot.infinity_polling(skip_pending=True)
