import os
import subprocess
import sys
import azure.cognitiveservices.speech as speechsdk
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    filters, ContextTypes
)
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from database import SessionLocal
from models import Vendor, Transaction
from parser import parse_transaction
from summaries import daily_summary, weekly_summary
from tts import synthesize_speech

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

app = FastAPI()
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Conversation states for onboarding
ASK_NAME, ASK_SELLS = range(2)


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


async def transcribe_incoming_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Helper: download + convert + transcribe a voice message the user just sent. Returns text or None/''."""
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    os.makedirs("data/incoming_voice", exist_ok=True)
    ogg_path = f"data/incoming_voice/{voice.file_id}.ogg"
    wav_path = f"data/incoming_voice/{voice.file_id}.wav"
    await file.download_to_drive(ogg_path)
    convert_ogg_to_wav(ogg_path, wav_path)
    return transcribe_wav(wav_path)


def get_or_create_vendor(db, chat_id: str) -> Vendor:
    vendor = db.query(Vendor).filter(Vendor.telegram_chat_id == chat_id).first()
    if vendor is None:
        vendor = Vendor(telegram_chat_id=chat_id)
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
    return vendor


def format_summary(summary: dict, title: str) -> str:
    return (
        f"{title}. "
        f"ሽያጭ {summary['total_sales']} ብር. "
        f"ወጪ {summary['total_expenses']} ብር. "
        f"ዱቤ {summary['total_debt']} ብር. "
        f"ተጣራ ትርፍ {summary['net_profit']} ብር።"
    )


async def reply_with_voice(update: Update, text: str):
    audio_path = synthesize_speech(text)
    if audio_path:
        with open(audio_path, "rb") as audio_file:
            await update.message.reply_voice(voice=audio_file)
    else:
        await update.message.reply_text(text)


# ---------- Onboarding conversation ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        vendor = db.query(Vendor).filter(Vendor.telegram_chat_id == chat_id).first()
        if vendor and vendor.name and vendor.sells:
            # Already onboarded — just greet
            await update.message.reply_text(
                f"እንኳን ደህና መጡ፣ {vendor.name}! ሽያጭዎን በድምጽ ብቻ ይናገሩ።"
            )
            return ConversationHandler.END
    finally:
        db.close()

    await update.message.reply_text(
        "እንኳን ደህና መጡ! ወደ ገበያ ደብተር በድምጽ የሽያጭ መዝገብ ቦት። እባክዎ ስምዎን ይንገሩኝ (በጽሁፍ ወይም በድምጽ)።"
    )
    return ASK_NAME


async def ask_name_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.voice:
        name = await transcribe_incoming_voice(update, context)
    else:
        name = update.message.text

    if not name:
        await update.message.reply_text("አልተሰማም፣ እባክዎ ስምዎን ደግመው ይንገሩኝ።")
        return ASK_NAME

    context.user_data["pending_name"] = name.strip()
    await update.message.reply_text(f"አመሰግናለሁ {name}! ምን ዓይነት እቃ ነው የሚሸጡት?")
    return ASK_SELLS


async def ask_sells_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.voice:
        sells = await transcribe_incoming_voice(update, context)
    else:
        sells = update.message.text

    if not sells:
        await update.message.reply_text("አልተሰማም፣ እባክዎ ደግመው ይንገሩኝ።")
        return ASK_SELLS

    chat_id = str(update.effective_chat.id)
    name = context.user_data.get("pending_name")

    db = SessionLocal()
    try:
        vendor = get_or_create_vendor(db, chat_id)
        vendor.name = name
        vendor.sells = sells.strip()
        db.commit()
    finally:
        db.close()

    await update.message.reply_text(
        f"ተመዝግበዋል {name}! ከአሁን ጀምሮ ሽያጭዎን በድምጽ ብቻ ይናገሩ።"
    )
    return ConversationHandler.END


async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ተሰርዟል። /start ብለው እንደገና ይጀምሩ።")
    return ConversationHandler.END


# ---------- Summaries ----------

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        vendor = get_or_create_vendor(db, chat_id)
        summary = daily_summary(db, vendor.id)
        await reply_with_voice(update, format_summary(summary, "የዛሬ ማጠቃለያ"))
    finally:
        db.close()


async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        vendor = get_or_create_vendor(db, chat_id)
        summary = weekly_summary(db, vendor.id)
        await reply_with_voice(update, format_summary(summary, "የሳምንት ማጠቃለያ"))
    finally:
        db.close()


# ---------- Main voice transaction handler ----------

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    transcribed_text = await transcribe_incoming_voice(update, context)

    if transcribed_text is None:
        await reply_with_voice(update, "ይቅርታ፣ ስህተት ተፈጥሯል። እባክዎ ደግመው ይሞክሩ።")
        return
    elif transcribed_text == "":
        await reply_with_voice(update, "አልተሰማም፣ እባክዎ ደግመው ይናገሩ።")
        return

    await update.message.reply_text(f"📝 {transcribed_text}")

    result = parse_transaction(transcribed_text)

    if result.get("status") == "needs_clarification":
        await reply_with_voice(update, result.get("question"))
        return

    if result.get("status") != "ok":
        await reply_with_voice(update, "ይቅርታ፣ መረዳት አልቻልኩም። እባክዎ ደግመው ይሞክሩ።")
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

        confirmation_text = f"{result.get('item') or ''} {result.get('amount')} ብር ተመዝግቧል።"
        await reply_with_voice(update, confirmation_text)
    finally:
        db.close()


# ---------- Handlers setup ----------

onboarding_conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ASK_NAME: [MessageHandler((filters.TEXT | filters.VOICE) & ~filters.COMMAND, ask_name_response)],
        ASK_SELLS: [MessageHandler((filters.TEXT | filters.VOICE) & ~filters.COMMAND, ask_sells_response)],
    },
    fallbacks=[CommandHandler("cancel", cancel_onboarding)],
)

telegram_app.add_handler(onboarding_conv)
telegram_app.add_handler(CommandHandler("today", today))
telegram_app.add_handler(CommandHandler("week", week))
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
