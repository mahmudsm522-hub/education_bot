# education_bot_interactive.py
import os
import json
from flask import Flask, request
import telebot

# ================= CONFIG =================
TOKEN = "YOUR_BOT_TOKEN"  # za ka canza daga @BotFather
ADMIN_ID = 6648308251       # saka Telegram User ID ɗinka
RENDER_URL = "https://your-render-url.onrender.com"

bot = telebot.TeleBot(TOKEN)

# ================= USERS STORAGE =================
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users_dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users_dict, f)

users = load_users()

# ================= FLASK APP =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running ✅"

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# ================= TELEGRAM HANDLERS =================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name
    if user_id not in users:
        users[user_id] = {"username": username, "score": 0, "current_lesson": None}
        save_users(users)
    bot.reply_to(message, f"Hello {username}! Use /lesson to start learning!")

@bot.message_handler(commands=['lesson'])
def lesson(message):
    bot.send_message(message.chat.id, "This is your first lesson! Reply with your answer.")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    bot.reply_to(message, f"You said: {message.text}")

# ================= RUN WEBHOOK =================
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"Webhook set to {webhook_url}")

    app.run(host="0.0.0.0", port=PORT)
