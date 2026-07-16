import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

print("KEY LOADED:", os.getenv("GROQ_API_KEY")[:10], "...")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

audio_folder = "data/test_audio"
files = sorted(os.listdir(audio_folder))

print("=== GROQ WHISPER RESULTS ===\n")

for filename in files:
    filepath = os.path.join(audio_folder, filename)
    with open(filepath, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=(filename, audio_file.read()),
            model="whisper-large-v3",
            
        )
    print(f"{filename}: {transcription.text}\n")