import os
import telebot
from telebot import types
from fpdf import FPDF
from flask import Flask, request
from datetime import datetime

# ================== CONFIG ==================
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
RENDER_URL = os.getenv("RENDER_URL")  # Example: https://telegram-education-bot-b1qt.onrender.com

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ================== DATA ==================
users = {}

python_lessons = [
    "📘 Lesson 1: print()\n\nprint('Hello World')",
    "📘 Lesson 2: Variables\n\nx = 5\ny = 10\nprint(x + y)",
    "📘 Lesson 3: Lists\n\nmylist = [1,2,3]\nprint(mylist)",
]

# ================== HELPERS ==================
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📚 Python Lessons", "👤 Profile")
    kb.add("🌐 Channels / Social")
    kb.add("ℹ️ About", "🔐 Admin Panel")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Add Lesson")
    kb.add("⬅️ Back to Main Menu")
    return kb

def generate_python_pdf(chat_id):
    username = users[chat_id]["username"]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Python Course Certificate for {username}", ln=True)
    filename = f"python_course_{chat_id}.pdf"
    pdf.output(filename)
    bot.send_document(chat_id, open(filename, "rb"))
    os.remove(filename)

# ================== COMMANDS ==================
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "👋 Welcome! Enter your username:")
    bot.register_next_step_handler(msg, get_username)

def get_username(message):
    chat_id = message.chat.id
    username = message.text.strip()
    users[chat_id] = {"username": username, "lesson": 0}
    msg = bot.send_message(chat_id, "🔑 Enter password (any text):")
    bot.register_next_step_handler(msg, get_password)

def get_password(message):
    chat_id = message.chat.id
    users[chat_id]["password"] = message.text.strip()
    bot.send_message(chat_id, f"✅ Welcome {users[chat_id]['username']}!", reply_markup=main_menu())

# ================== MENU HANDLERS ==================
@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(message):
    chat_id = message.chat.id
    if chat_id not in users:
        bot.send_message(chat_id, "⚠️ Use /start first")
        return
    u = users[chat_id]
    bot.send_message(chat_id, f"👤 Name: {u['username']}\n📘 Python Lesson: {u['lesson']}/{len(python_lessons)}")

@bot.message_handler(func=lambda m: m.text == "📚 Python Lessons")
def start_python(message):
    chat_id = message.chat.id
    if chat_id not in users:
        bot.send_message(chat_id, "⚠️ Use /start first")
        return
    send_lesson(chat_id)

def send_lesson(chat_id):
    idx = users[chat_id]["lesson"]
    if idx >= len(python_lessons):
        bot.send_message(chat_id, "🎉 You finished all Python lessons! Generating PDF...")
        generate_python_pdf(chat_id)
        bot.send_message(chat_id, "⬅️ Back to menu", reply_markup=main_menu())
        return
    text = python_lessons[idx]
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➡️ Next Lesson", "⬅️ Back to Main Menu")
    bot.send_message(chat_id, text, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "➡️ Next Lesson")
def next_lesson(message):
    chat_id = message.chat.id
    users[chat_id]["lesson"] += 1
    send_lesson(chat_id)

@bot.message_handler(func=lambda m: m.text == "⬅️ Back to Main Menu")
def back_menu(message):
    bot.send_message(message.chat.id, "Main Menu", reply_markup=main_menu())

# ================== SOCIAL / ABOUT ==================
@bot.message_handler(func=lambda m: m.text == "🌐 Channels / Social")
def social_links(message):
    chat_id = message.chat.id
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Telegram", url="https://t.me/Mahmudsm1"))
    kb.add(types.InlineKeyboardButton("X (Twitter)", url="https://x.com/Mahmud_sm1"))
    kb.add(types.InlineKeyboardButton("Facebook", url="https://www.facebook.com/share/1GWma4DRsg/"))
    bot.send_message(chat_id, "🌐 Connect with us:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "ℹ️ About")
def about(message):
    chat_id = message.chat.id
    bot.send_message(chat_id,
        "Hi! I'm an Education Bot designed to help you learn Python and other subjects. "
        "Lessons and content are regularly updated. "
        "You can reach me directly on Telegram: @MHSM5", reply_markup=main_menu()
    )

# ================== ADMIN PANEL ==================
@bot.message_handler(func=lambda m: m.text == "🔐 Admin Panel")
def admin_panel(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID:
        bot.send_message(chat_id, "❌ You are not admin.")
        return
    bot.send_message(chat_id, "Admin Panel", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "➕ Add Lesson")
def add_lesson(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID:
        return
    msg = bot.send_message(chat_id, "Send new lesson text:")
    bot.register_next_step_handler(msg, save_lesson)

def save_lesson(message):
    python_lessons.append(message.text.strip())
    bot.send_message(message.chat.id, f"✅ New lesson added! Total lessons: {len(python_lessons)}", reply_markup=admin_menu())

# ================== FLASK WEBHOOK ==================
@app.route("/")
def home():
    return "Bot is running ✅"

@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# ================== START SERVER ==================
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print("Webhook set to:", webhook_url)
    app.run(host="0.0.0.0", port=PORT)
