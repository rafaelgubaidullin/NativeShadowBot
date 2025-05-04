import os
import tempfile
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.ext.webhook import WebhookServer

# --- CONFIG ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = "TxGEqnHWrfWFTfGW9XjX"
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST")  # пример: "https://your-app-name.onrender.com"

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY is not set")
if not WEBHOOK_HOST:
    raise ValueError("WEBHOOK_HOST is not set")


# --- SPEECH GENERATION ---
def generate_speech(text: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.content


# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to NativeShadow Bot!\n\n"
        "Send me any English text, and I’ll reply with a native voice 🎙.\n"
        "Great for shadowing practice.\n\n"
        "Ready to train your accent? Just type a sentence!"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if not user_text:
        await update.message.reply_text("❗️Please send some text to generate audio.")
        return

    await update.message.reply_text("🎙 Generating audio, please wait...")

    try:
        audio_data = generate_speech(user_text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        await update.message.reply_voice(voice=open(tmp_path, "rb"))
        await update.message.reply_text("Voice: 🎙 Josh (male, native American)")
        os.remove(tmp_path)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error occurred: {e}")


# --- FLASK APP + TELEGRAM ---
flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    return "Bot is running!"


@flask_app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return "ok"


# --- MAIN ---
bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

if __name__ == "__main__":
    # Установить Webhook
    bot.delete_webhook()
    bot.set_webhook(url=f"{WEBHOOK_HOST}/webhook/{TELEGRAM_TOKEN}")

    print("✅ Webhook set, bot is running!")
    flask_app.run(host="0.0.0.0", port=10000)