import os
import telebot
from telebot import types
from fpdf import FPDF
from flask import Flask, request
from datetime import datetime

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

physics_questions = [
    {"q": "What is the unit of force?", "a": "newton"},
    {"q": "Acceleration due to gravity on Earth?", "a": "9.8"},
    {"q": "Formula: F = ma. What does 'm' mean?", "a": "mass"},
    {"q": "SI unit of energy?", "a": "joule"},
]

# ================== MENUS ==================
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📚 Python Lessons", "🧲 Physics Quiz")
    kb.add("👤 Profile", "🔐 Admin Panel")
    kb.add("📢 Join Telegram Channel", "🐦 Follow on X")
    kb.add("📘 Facebook Page", "ℹ️ About")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Add Lesson")
    kb.add("⬅️ Back to Main Menu")
    return kb

# ================== START ==================
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    users[chat_id] = {
        "username": message.from_user.first_name or "Student",
        "lesson": 0
    }
    bot.send_message(
        chat_id,
        "👋 Welcome to the Education Bot!\nUse the buttons below to learn and explore.",
        reply_markup=main_menu()
    )

# ================== ABOUT ==================
@bot.message_handler(func=lambda m: m.text == "ℹ️ About")
def about(message):
    text = (
        "👨‍💻 About Me\n\n"
        "I am passionate about learning and teaching different fields of knowledge such as programming, science, and technology.\n\n"
        "This bot is created to help students learn step by step. This is not the end — more lessons and more subjects will be added in the future as the journey of learning continues.\n\n"
        "📌 For direct contact on Telegram:\n"
        "👉 @MHSM5\n\n"
        "🚀 Keep learning, keep growing!"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# ================== SOCIAL LINKS ==================
@bot.message_handler(func=lambda m: m.text == "📢 Join Telegram Channel")
def tg_channel(message):
    bot.send_message(message.chat.id, "👉 Join our Telegram Channel:\nhttps://t.me/Mahmudsm1", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🐦 Follow on X")
def twitter(message):
    bot.send_message(message.chat.id, "👉 Follow on X (Twitter):\nhttps://x.com/Mahmud_sm1", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📘 Facebook Page")
def facebook(message):
    bot.send_message(message.chat.id, "👉 Visit our Facebook Page:\nhttps://www.facebook.com/share/1GWma4DRsg/", reply_markup=main_menu())

# ================== PROFILE ==================
@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(message):
    chat_id = message.chat.id
    u = users.get(chat_id)
    if not u:
        bot.send_message(chat_id, "⚠️ Use /start first")
        return
    bot.send_message(chat_id, f"👤 Name: {u['username']}\n📘 Lesson: {u['lesson']}/{len(python_lessons)}", reply_markup=main_menu())

# ================== PYTHON LESSONS ==================
@bot.message_handler(func=lambda m: m.text == "📚 Python Lessons")
def start_python(message):
    chat_id = message.chat.id
    send_lesson(chat_id)

def send_lesson(chat_id):
    idx = users[chat_id]["lesson"]
    if idx >= len(python_lessons):
        bot.send_message(chat_id, "🎉 You finished all lessons!", reply_markup=main_menu())
        return

    text = python_lessons[idx]
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➡️ Next Lesson")
    kb.add("⬅️ Back to Main Menu")
    bot.send_message(chat_id, text, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "➡️ Next Lesson")
def next_lesson(message):
    chat_id = message.chat.id
    users[chat_id]["lesson"] += 1
    send_lesson(chat_id)

@bot.message_handler(func=lambda m: m.text == "⬅️ Back to Main Menu")
def back_menu(message):
    bot.send_message(message.chat.id, "🏠 Main Menu", reply_markup=main_menu())

# ================== ADMIN ==================
@bot.message_handler(func=lambda m: m.text == "🔐 Admin Panel")
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ You are not admin.")
        return
    bot.send_message(message.chat.id, "👑 Welcome Admin", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "➕ Add Lesson")
def add_lesson(message):
    if message.chat.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "✍️ Send the new lesson text:")
    bot.register_next_step_handler(msg, save_lesson)

def save_lesson(message):
    if message.chat.id != ADMIN_ID:
        return
    python_lessons.append(message.text)
    bot.send_message(message.chat.id, "✅ New lesson added successfully!", reply_markup=admin_menu())

# ================== FLASK ==================
@app.route("/")
def home():
    return "Bot is running ✅"

@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# ================== START ==================
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))

    bot.remove_webhook()

    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TOKEN}"
        bot.set_webhook(url=webhook_url)
        print("Webhook set to:", webhook_url)

    app.run(host="0.0.0.0", port=PORT)
