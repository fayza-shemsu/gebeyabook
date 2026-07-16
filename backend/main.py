import os
import subprocess
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = FastAPI()
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()


def convert_ogg_to_wav(ogg_path: str, wav_path: str):
    """Convert a .ogg voice file to .wav (16kHz, mono) using ffmpeg."""
    subprocess.run([
        "ffmpeg", "-y",
        "-i", ogg_path,
        "-ar", "16000",
        "-ac", "1",
        wav_path
    ], check=True, capture_output=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = "እንኳን ደህና መጡ! ወደ ገበያ ደብተር በድምጽ የሽያጭ መዝገብ ቦት። ሽያጭዎን በድምጽ ብቻ ይናገሩ።"
    await update.message.reply_text(welcome_message)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    os.makedirs("data/incoming_voice", exist_ok=True)
    ogg_path = f"data/incoming_voice/{voice.file_id}.ogg"
    wav_path = f"data/incoming_voice/{voice.file_id}.wav"

    await file.download_to_drive(ogg_path)
    convert_ogg_to_wav(ogg_path, wav_path)

    await update.message.reply_text("ድምጽዎ ተቀብለናል! (Voice received)")
    print(f"Saved voice note: {ogg_path} -> converted to {wav_path}")


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.VOICE, handle_voice))


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


@app.get("/")
async def root():
    return {"status": "GebeyaBook bot is running"}


@app.on_event("startup")
async def startup():
    await telegram_app.initialize()
    await telegram_app.start()


@app.on_event("shutdown")
async def shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()