import os
import telebot
from telebot import types
from fpdf import FPDF
from flask import Flask, request

# ================== CONFIG ==================
TOKEN = os.getenv("TOKEN")  # Daga Render environment
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
RENDER_URL = os.getenv("RENDER_URL")  # Daga Render environment

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
    kb.add("📚 Python Lessons", "🧲 Physics Quiz")
    kb.add("👤 Profile", "🔐 Admin Panel")
    kb.add("🌐 Links")  # New links button
    return kb

def links_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Telegram", "X (Twitter)", "Facebook")
    kb.add("⬅️ Back to Main Menu")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📢 Broadcast", "➕ Add Lesson")
    kb.add("⬅️ Back to Main Menu")
    return kb

# ================== LOGIN ==================
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "👋 Welcome! Enter your username:")
    bot.register_next_step_handler(msg, get_username)

def get_username(message):
    chat_id = message.chat.id
    username = message.text.strip()
    users[chat_id] = {
        "username": username,
        "lesson": 0,
    }
    msg = bot.send_message(chat_id, "🔑 Enter password:")
    bot.register_next_step_handler(msg, get_password)

def get_password(message):
    chat_id = message.chat.id
    users[chat_id]["password"] = message.text.strip()
    bot.send_message(
        chat_id,
        f"✅ Welcome {users[chat_id]['username']}!\nUse the menu below to navigate.",
        reply_markup=main_menu()
    )

# ================== PROFILE ==================
@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(message):
    chat_id = message.chat.id
    if chat_id not in users:
        bot.send_message(chat_id, "⚠️ Use /start first")
        return
    u = users[chat_id]
    bot.send_message(chat_id,
        f"👤 Name: {u['username']}\n📘 Python Lesson: {u['lesson']}/{len(python_lessons)}"
    )

# ================== PYTHON LESSONS ==================
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
        generate_pdf(chat_id)
        bot.send_message(chat_id, "⬅️ Back to menu", reply_markup=main_menu())
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

# ================== PDF FUNCTIONS ==================
def generate_pdf(chat_id):
    username = users[chat_id]["username"]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Python Course Certificate for {username}", ln=True)

    filename = f"python_course_{chat_id}.pdf"
    pdf.output(filename)
    bot.send_document(chat_id, open(filename, "rb"))
    os.remove(filename)

# ================== LINKS ==================
@bot.message_handler(func=lambda m: m.text == "🌐 Links")
def links(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "🌐 Choose a platform:", reply_markup=links_menu())

@bot.message_handler(func=lambda m: m.text in ["Telegram", "X (Twitter)", "Facebook"])
def open_link(message):
    links_dict = {
        "Telegram": "https://t.me/Mahmudsm1",
        "X (Twitter)": "https://x.com/Mahmud_sm1",
        "Facebook": "https://www.facebook.com/share/1GWma4DRsg/"
    }
    bot.send_message(message.chat.id, f"🔗 {links_dict[message.text]}")

# ================== ADMIN ==================
@bot.message_handler(func=lambda m: m.text == "🔐 Admin Panel")
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ You are not admin.")
        return
    bot.send_message(message.chat.id, "Welcome Admin!", reply_markup=admin_menu())

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

    # SET WEBHOOK
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print("Webhook set to:", webhook_url)

    # Run Flask app
    app.run(host="0.0.0.0", port=PORT)
