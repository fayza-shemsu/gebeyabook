import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

speech_key = os.getenv("AZURE_SPEECH_KEY")
speech_region = os.getenv("AZURE_SPEECH_REGION")

audio_folder = "data/test_audio"
files = sorted(f for f in os.listdir(audio_folder) if f.endswith(".wav"))

print("=== AZURE SPEECH-TO-TEXT RESULTS ===\n")

for filename in files:
    filepath = os.path.join(audio_folder, filename)
    
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_recognition_language = "am-ET"
    audio_config = speechsdk.audio.AudioConfig(filename=filepath)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    result = recognizer.recognize_once()
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"{filename}: {result.text}\n")
    else:
        print(f"{filename}: [FAILED — {result.reason}]\n")