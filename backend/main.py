import os
import subprocess
import sys
import azure.cognitiveservices.speech as speechsdk
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.error import TelegramError
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    filters, ContextTypes
)
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

sys.path.insert(0, os.path.dirname(__file__))
from database import SessionLocal
from models import Vendor, Transaction
from parser import parse_transaction
from summaries import daily_summary, weekly_summary, debts_summary, get_last_transaction
from tts import synthesize_speech

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

app = FastAPI()
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

ASK_NAME, ASK_SELLS = range(2)
EDIT_FIELD, EDIT_VALUE = range(2, 4)

MISTAKE_KEYWORDS = ["ስሕተት", "ስህተት"]


def convert_ogg_to_wav(ogg_path: str, wav_path: str):
    subprocess.run([
        "ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path
    ], check=True, capture_output=True, timeout=20)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
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
        raise RuntimeError(f"STT failed: {result.reason}")


async def transcribe_incoming_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    os.makedirs("data/incoming_voice", exist_ok=True)
    ogg_path = f"data/incoming_voice/{voice.file_id}.ogg"
    wav_path = f"data/incoming_voice/{voice.file_id}.wav"
    await file.download_to_drive(ogg_path)
    convert_ogg_to_wav(ogg_path, wav_path)
    try:
        return transcribe_wav(wav_path)
    except Exception:
        return None


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


def format_debts(debts: list) -> str:
    if not debts:
        return "ምንም ያልተከፈለ ዱቤ የለም።"
    parts = ["ያልተከፈለ ዱቤ:"]
    for d in debts:
        parts.append(f"{d['customer_name']} {d['total_owed']} ብር")
    return ". ".join(parts) + "።"


def onboarding_complete_message(name: str) -> str:
    lines = [
        f"ተመዝግበዋል {name}! ከአሁን ጀምሮ ሽያጭዎን በድምጽ ብቻ ይናገሩ።",
        "",
        "ምሳሌ: ሽንኩርት ሁለት ኪሎ ሁለት መቶ ብር ሸጥኩ",
        "",
        "/today - የዛሬ ሽያጭ",
        "/week - የሳምንት ሽያጭ",
        "/debts - ያልተከፈለ ዱቤ",
    ]
    return "\n".join(lines)


async def reply_with_voice(update: Update, text: str):
    try:
        audio_path = synthesize_speech(text)
    except Exception:
        audio_path = None

    if audio_path:
        try:
            with open(audio_path, "rb") as audio_file:
                await update.message.reply_voice(voice=audio_file)
            return
        except TelegramError:
            pass
    try:
        await update.message.reply_text(text)
    except TelegramError:
        pass


# ---------- Undo helper (shared by voice trigger and /undo command) ----------

async def perform_undo(update: Update, chat_id: str):
    db = SessionLocal()
    try:
        vendor = get_or_create_vendor(db, chat_id)
        last_tx = get_last_transaction(db, vendor.id)
        if last_tx is None:
            await reply_with_voice(update, "የሚሰረዝ ምንም ግብይት የለም።")
            return
        item_desc = last_tx.item or (last_tx.customer_name or "")
        amount = last_tx.amount
        db.delete(last_tx)
        db.commit()
        await reply_with_voice(update, f"{item_desc} {amount} ብር ተሰርዟል።")
    finally:
        db.close()


# ---------- Onboarding conversation ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        vendor = db.query(Vendor).filter(Vendor.telegram_chat_id == chat_id).first()
        if vendor and vendor.name and vendor.sells:
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

    await update.message.reply_text(onboarding_complete_message(name))
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


async def debts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        vendor = get_or_create_vendor(db, chat_id)
        debt_list = debts_summary(db, vendor.id)
        await reply_with_voice(update, format_debts(debt_list))
    finally:
        db.close()


async def undo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await perform_undo(update, chat_id)


# ---------- /edit_last conversation ----------

async def edit_last_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        vendor = get_or_create_vendor(db, chat_id)
        last_tx = get_last_transaction(db, vendor.id)
        if last_tx is None:
            await update.message.reply_text("የሚስተካከል ምንም ግብይት የለም።")
            return ConversationHandler.END
        context.user_data["editing_tx_id"] = last_tx.id
        await update.message.reply_text(
            f"የመጨረሻው ግብይት: {last_tx.item or last_tx.customer_name or ''} {last_tx.amount} ብር።\n"
            f"ምን ማስተካከል ይፈልጋሉ? 'ዋጋ' ወይም 'እቃ' ይበሉ።"
        )
        return EDIT_FIELD
    finally:
        db.close()


async def edit_field_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.voice:
        field_text = await transcribe_incoming_voice(update, context)
    else:
        field_text = update.message.text

    if not field_text:
        await update.message.reply_text("አልተሰማም፣ 'ዋጋ' ወይም 'እቃ' ይበሉ።")
        return EDIT_FIELD

    field_text = field_text.strip()
    if "ዋጋ" in field_text or "ብር" in field_text:
        context.user_data["editing_field"] = "amount"
        await update.message.reply_text("አዲሱ ዋጋ ስንት ብር ነው?")
    elif "እቃ" in field_text:
        context.user_data["editing_field"] = "item"
        await update.message.reply_text("አዲሱ የእቃ ስም ማን ነው?")
    else:
        await update.message.reply_text("አልገባኝም፣ 'ዋጋ' ወይም 'እቃ' ይበሉ።")
        return EDIT_FIELD

    return EDIT_VALUE


async def edit_value_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.voice:
        new_value = await transcribe_incoming_voice(update, context)
    else:
        new_value = update.message.text

    if not new_value:
        await update.message.reply_text("አልተሰማም፣ እባክዎ ደግመው ይናገሩ።")
        return EDIT_VALUE

    tx_id = context.user_data.get("editing_tx_id")
    field = context.user_data.get("editing_field")

    db = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
        if tx is None:
            await update.message.reply_text("ስህተት፣ ግብይቱ አልተገኘም።")
            return ConversationHandler.END

        if field == "amount":
            digits = "".join(c for c in new_value if c.isdigit())
            if not digits:
                await update.message.reply_text("ቁጥር አልገባኝም፣ እባክዎ ቁጥር ብቻ ይናገሩ።")
                return EDIT_VALUE
            tx.amount = float(digits)
        elif field == "item":
            tx.item = new_value.strip()

        db.commit()
        await reply_with_voice(update, f"ተስተካክሏል: {tx.item or ''} {tx.amount} ብር።")
    finally:
        db.close()

    context.user_data.pop("editing_tx_id", None)
    context.user_data.pop("editing_field", None)
    return ConversationHandler.END


async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ተሰርዟል።")
    return ConversationHandler.END


# ---------- Save a completed parsed transaction ----------

async def save_transaction(update: Update, chat_id: str, transcribed_text: str, result: dict):
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
        if result.get("type") == "debt":
            confirmation_text = f"ዱቤ ለ{result.get('customer_name') or ''} {result.get('amount')} ብር ተመዝግቧል።"
        else:
            confirmation_text = f"{result.get('item') or ''} {result.get('amount')} ብር ተመዝግቧል።"
        await reply_with_voice(update, confirmation_text)
    finally:
        db.close()


# ---------- Main voice transaction handler ----------

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    transcribed_text = await transcribe_incoming_voice(update, context)

    if transcribed_text is None:
        await reply_with_voice(update, "ይቅርታ፣ የግንኙነት ችግር ተፈጥሯል። እባክዎ ደግመው ይላኩ።")
        return
    elif transcribed_text == "":
        await reply_with_voice(update, "አልተሰማም፣ እባክዎ ደግመው ይናገሩ።")
        return

    await update.message.reply_text(f"📝 {transcribed_text}")

    if any(kw in transcribed_text for kw in MISTAKE_KEYWORDS):
        await perform_undo(update, chat_id)
        return

    pending = context.user_data.get("pending_clarification")
    if pending:
        combined_text = f"{pending['original_text']} {transcribed_text}"
        context.user_data.pop("pending_clarification", None)
    else:
        combined_text = transcribed_text

    result = parse_transaction(combined_text)

    if result.get("status") == "needs_clarification":
        context.user_data["pending_clarification"] = {"original_text": combined_text}
        await reply_with_voice(update, result.get("question") or "ስንት ብር ነው?")
        return

    if result.get("status") != "ok":
        await reply_with_voice(update, "ይቅርታ፣ መረዳት አልቻልኩም። እባክዎ ደግመው ይሞክሩ።")
        return

    await save_transaction(update, chat_id, combined_text, result)


# ---------- Handlers setup ----------

onboarding_conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ASK_NAME: [MessageHandler((filters.TEXT | filters.VOICE) & ~filters.COMMAND, ask_name_response)],
        ASK_SELLS: [MessageHandler((filters.TEXT | filters.VOICE) & ~filters.COMMAND, ask_sells_response)],
    },
    fallbacks=[CommandHandler("cancel", cancel_onboarding)],
)

edit_last_conv = ConversationHandler(
    entry_points=[CommandHandler("edit_last", edit_last_start)],
    states={
        EDIT_FIELD: [MessageHandler((filters.TEXT | filters.VOICE) & ~filters.COMMAND, edit_field_response)],
        EDIT_VALUE: [MessageHandler((filters.TEXT | filters.VOICE) & ~filters.COMMAND, edit_value_response)],
    },
    fallbacks=[CommandHandler("cancel", cancel_edit)],
)

telegram_app.add_handler(onboarding_conv)
telegram_app.add_handler(edit_last_conv)
telegram_app.add_handler(CommandHandler("today", today))
telegram_app.add_handler(CommandHandler("week", week))
telegram_app.add_handler(CommandHandler("debts", debts))
telegram_app.add_handler(CommandHandler("undo", undo_command))
telegram_app.add_handler(MessageHandler(filters.VOICE, handle_voice))


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
    except Exception as e:
        print(f"Webhook error (swallowed to avoid crash): {e}")
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
