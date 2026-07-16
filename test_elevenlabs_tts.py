import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")

# Using a multilingual voice - "Rachel" or any multilingual voice ID
voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - multilingual v2 supports many languages

url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

headers = {
    "xi-api-key": api_key,
    "Content-Type": "application/json"
}

data = {
    "text": "ሽንኩርት ሁለት መቶ ብር ተመዝግቧል",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.75
    }
}

response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    with open("data/test_audio/elevenlabs_tts_output.mp3", "wb") as f:
        f.write(response.content)
    print("ElevenLabs TTS saved to data/test_audio/elevenlabs_tts_output.mp3")
else:
    print(f"Failed: {response.status_code} - {response.text}")