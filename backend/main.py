import os
import subprocess
import azure.cognitiveservices.speech as speechsdk
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

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


def transcribe_wav(wav_path: str) -> str:
    """Send a .wav file to Azure Speech-to-Text (Amharic) and return the transcribed text."""
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
        return None  # signals an error


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

    transcribed_text = transcribe_wav(wav_path)

    if transcribed_text is None:
        await update.message.reply_text("ይቅርታ፣ ስህተት ተፈጥሯል። እባክዎ ደግመው ይሞክሩ። (Error, please try again)")
    elif transcribed_text == "":
        await update.message.reply_text("አልተሰማም፣ እባክዎ ደግመው ይናገሩ። (Didn't catch that, please repeat)")
    else:
        await update.message.reply_text(f"📝 {transcribed_text}")

    print(f"Voice: {ogg_path} -> Transcription: {transcribed_text}")


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