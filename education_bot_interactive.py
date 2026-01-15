import os
import telebot
from telebot import types
from flask import Flask, request

# ================== CONFIG ==================
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
RENDER_URL = os.getenv("RENDER_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ================== DATA ==================
users = {}

python_lessons = [
    "📘 Lesson 1: print()\n\nprint('Hello World')",
    "📘 Lesson 2: Variables\n\nx = 5\ny = 10\nprint(x + y)",
    "📘 Lesson 3: List\n\nmylist = [1,2,3]\nprint(mylist)",
]

# ================== KEYBOARDS ==================
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📚 Python Lessons")
    kb.add("📢 Join Telegram Channel", "🐦 Follow on X")
    kb.add("📘 Facebook Page", "ℹ️ About")
    kb.add("👤 Profile", "🔐 Admin Panel")
    return kb

# ================== START ==================
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        "👋 Welcome to Mahmud's Education Bot!\n\nChoose an option below:",
        reply_markup=main_menu()
    )

# ================== ABOUT ==================
@bot.message_handler(func=lambda m: m.text == "ℹ️ About")
def about(message):
    text = (
        "👋 Hi, I'm Mahmud.\n\n"
        "This bot is created to help people learn different subjects like programming and more.\n"
        "This is not the end — more lessons and subjects will be added in the future.\n\n"
        "📩 Contact me on Telegram: @MHSM5"
    )
    bot.send_message(message.chat.id, text)

# ================== LINKS ==================
@bot.message_handler(func=lambda m: m.text == "📢 Join Telegram Channel")
def tg_channel(message):
    bot.send_message(message.chat.id, "👉 Join our Telegram channel:\nhttps://t.me/Mahmudsm1")

@bot.message_handler(func=lambda m: m.text == "🐦 Follow on X")
def x_link(message):
    bot.send_message(message.chat.id, "👉 Follow me on X (Twitter):\nhttps://x.com/Mahmud_sm1")

@bot.message_handler(func=lambda m: m.text == "📘 Facebook Page")
def fb_link(message):
    bot.send_message(message.chat.id, "👉 Follow our Facebook page:\nhttps://www.facebook.com/share/1GWma4DRsg/")

# ================== PYTHON LESSONS ==================
@bot.message_handler(func=lambda m: m.text == "📚 Python Lessons")
def python_lessons_start(message):
    text = "📘 Python Lessons:\n\n" + "\n\n".join(python_lessons)
    bot.send_message(message.chat.id, text)

# ================== PROFILE ==================
@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(message):
    bot.send_message(message.chat.id, f"👤 Your ID: {message.chat.id}")

# ================== ADMIN ==================
@bot.message_handler(func=lambda m: m.text == "🔐 Admin Panel")
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ You are not admin.")
        return
    bot.send_message(message.chat.id, "✅ Welcome Admin.\n(More admin features coming soon)")

# ================== FLASK ROUTES ==================
@app.route("/")
def home():
    return "Bot is running ✅"

@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# ================== STARTUP ==================
def setup_webhook():
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print("Webhook set to:", webhook_url)

setup_webhook()

# ================== FOR GUNICORN ==================
# Gunicorn will look for: app
# Do NOT use app.run() here
