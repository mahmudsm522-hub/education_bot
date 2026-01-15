import os
import telebot
from telebot import types
from fpdf import FPDF
from flask import Flask, request
from datetime import datetime
from threading import Thread
import requests
import time

# ================== CONFIG ==================
TOKEN = os.getenv("TOKEN")  # Bot token daga Render
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
RENDER_URL = os.getenv("RENDER_URL")  # Misali: https://telegram-education-bot-b1qt.onrender.com

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

# ================== HELPERS ==================
def calculate_grade(score, total):
    pct = (score / total) * 100
    if pct >= 80:
        return "A"
    elif pct >= 60:
        return "B"
    elif pct >= 40:
        return "C"
    else:
        return "Fail"

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📚 Python Lessons", "🧲 Physics Quiz")
    kb.add("👤 Profile", "🔐 Admin Panel")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📢 Broadcast")
    kb.add("⬅️ Back to Main Menu")
    return kb

# ================== START ==================
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "👋 Welcome! Enter your name:")
    bot.register_next_step_handler(msg, get_username)

def get_username(message):
    chat_id = message.chat.id
    username = message.text.strip()

    users[chat_id] = {
        "username": username,
        "lesson": 0,
        "physics_score": 0,
        "physics_q_index": 0,
        "attempts": 0
    }

    bot.send_message(chat_id, f"✅ Welcome {username}!", reply_markup=main_menu())

# ================== PROFILE ==================
@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(message):
    chat_id = message.chat.id
    if chat_id not in users:
        bot.send_message(chat_id, "⚠️ Use /start first")
        return
    u = users[chat_id]
    bot.send_message(chat_id, f"👤 Name: {u['username']}\n📘 Python Lesson: {u['lesson']}/{len(python_lessons)}")

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
        bot.send_message(chat_id, "🎉 You finished all Python lessons! Generating your PDF...")
        generate_python_pdf(chat_id)
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

# ================== PDF ==================
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

# ================== PHYSICS QUIZ ==================
@bot.message_handler(func=lambda m: m.text == "🧲 Physics Quiz")
def start_physics(message):
    chat_id = message.chat.id
    if chat_id not in users:
        bot.send_message(chat_id, "⚠️ Use /start first")
        return

    users[chat_id]["physics_q_index"] = 0
    users[chat_id]["physics_score"] = 0
    users[chat_id]["attempts"] = 0
    ask_physics_question(chat_id)

def ask_physics_question(chat_id):
    idx = users[chat_id]["physics_q_index"]
    if idx >= len(physics_questions):
        score = users[chat_id]["physics_score"]
        total = len(physics_questions)
        bot.send_message(chat_id, f"🎓 Quiz finished! Score: {score}/{total}")
        bot.send_message(chat_id, "⬅️ Back to menu", reply_markup=main_menu())
        return

    q = physics_questions[idx]["q"]
    msg = bot.send_message(chat_id, f"❓ Question {idx+1}: {q}")
    bot.register_next_step_handler(msg, check_physics_answer)

def check_physics_answer(message):
    chat_id = message.chat.id
    idx = users[chat_id]["physics_q_index"]
    correct = physics_questions[idx]["a"].lower()
    answer = message.text.strip().lower()

    if answer == correct:
        users[chat_id]["physics_score"] += 1
        users[chat_id]["physics_q_index"] += 1
        users[chat_id]["attempts"] = 0
        bot.send_message(chat_id, "✅ Correct!")
    else:
        users[chat_id]["attempts"] += 1
        if users[chat_id]["attempts"] >= 3:
            bot.send_message(chat_id, f"❌ Failed! Correct answer was: {correct}")
            users[chat_id]["physics_q_index"] += 1
            users[chat_id]["attempts"] = 0
        else:
            bot.send_message(chat_id, f"⚠️ Wrong! Try again. Attempts left: {3 - users[chat_id]['attempts']}")
            ask_physics_question(chat_id)
            return

    ask_physics_question(chat_id)

# ================== ADMIN ==================
@bot.message_handler(func=lambda m: m.text == "🔐 Admin Panel")
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ You are not admin.")
        return
    bot.send_message(message.chat.id, "Welcome Admin!", reply_markup=admin_menu())

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

# ================== KEEP ALIVE ==================
def keep_alive():
    if not RENDER_URL:
        return
    while True:
        try:
            requests.get(f"{RENDER_URL}/")
        except:
            pass
        time.sleep(600)

# ================== START ==================
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))

    # SET WEBHOOK
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print("Webhook set to:", webhook_url)

    # Start bot polling in thread
    def start_bot():
        print("🤖 Bot is running...")
        bot.infinity_polling(skip_pending=True, timeout=30)

    Thread(target=start_bot).start()

    # Keep alive thread
    Thread(target=keep_alive, daemon=True).start()

    # Start Flask
    app.run(host="0.0.0.0", port=PORT)
