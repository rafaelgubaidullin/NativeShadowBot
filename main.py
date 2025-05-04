import os
import tempfile
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler




async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to NativeShadow Bot!\n\n"
        "Send me any English text, and I’ll reply with a native voice 🎙.\n"
        "Great for shadowing practice.\n\n"
        "Ready to train your accent? Just type a sentence!"
    )


# --- CONFIG ---
TELEGRAM_TOKEN = os.environ.get("7681510836:AAGWN6z3QohN_sqFBFnTx_rTmxG1Ge2YqvE")
ELEVENLABS_API_KEY = os.environ.get("sk_a15f49691c4b11b1a761f56dfce21676e7d5ba7842fd5df0")
VOICE_ID = "TxGEqnHWrfWFTfGW9XjX"

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

# --- TELEGRAM HANDLER ---
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

# --- START BOT ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🤖 Shadow bot is running...")
    app.run_polling()