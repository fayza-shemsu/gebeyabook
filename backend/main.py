import os
import subprocess
import sys
import azure.cognitiveservices.speech as speechsdk
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from database import SessionLocal
from models import Vendor, Transaction
from parser import parse_transaction

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

app = FastAPI()
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()


def convert_ogg_to_wav(ogg_path: str, wav_path: str):
    subprocess.run([
        "ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path
    ], check=True, capture_output=True)


def transcribe_wav(wav_path: str) -> str:
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_recognition_language = "am-ET"
    audio_config = speechsdk.audio.AudioConfig(filename=wav_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return ""
    else:
        return None


def get_or_create_vendor(db, chat_id: str) -> Vendor:
    vendor = db.query(Vendor).filter(Vendor.telegram_chat_id == chat_id).first()
    if vendor is None:
        vendor = Vendor(telegram_chat_id=chat_id)
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
    return vendor


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = "እንኳን ደህና መጡ! ወደ ገበያ ደብተር በድምጽ የሽያጭ መዝገብ ቦት። ሽያጭዎን በድምጽ ብቻ ይናገሩ።"
    await update.message.reply_text(welcome_message)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    os.makedirs("data/incoming_voice", exist_ok=True)
    ogg_path = f"data/incoming_voice/{voice.file_id}.ogg"
    wav_path = f"data/incoming_voice/{voice.file_id}.wav"

    await file.download_to_drive(ogg_path)
    convert_ogg_to_wav(ogg_path, wav_path)

    transcribed_text = transcribe_wav(wav_path)

    if transcribed_text is None:
        await update.message.reply_text("ይቅርታ፣ ስህተት ተፈጥሯል። እባክዎ ደግመው ይሞክሩ።")
        return
    elif transcribed_text == "":
        await update.message.reply_text("አልተሰማም፣ እባክዎ ደግመው ይናገሩ።")
        return

    result = parse_transaction(transcribed_text)

    if result.get("status") == "needs_clarification":
        await update.message.reply_text(f"📝 {transcribed_text}\n\n❓ {result.get('question')}")
        return

    if result.get("status") != "ok":
        await update.message.reply_text(f"📝 {transcribed_text}\n\n⚠️ Could not process, please try again.")
        return

    db = SessionLocal()
    try:
        vendor = get_or_create_vendor(db, chat_id)
        transaction = Transaction(
            vendor_id=vendor.id,
            type=result.get("type"),
            item=result.get("item"),
            amount=result.get("amount"),
            customer_name=result.get("customer_name"),
            note=result.get("note"),
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        await update.message.reply_text(
            f"📝 {transcribed_text}\n\n✅ ተመዝግቧል: {result.get('type')} — {result.get('item') or ''} {result.get('amount')} ብር"
        )
    finally:
        db.close()


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
