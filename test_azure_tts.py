import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

speech_key = os.getenv("AZURE_SPEECH_KEY")
speech_region = os.getenv("AZURE_SPEECH_REGION")

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
speech_config.speech_synthesis_voice_name = "am-ET-MekdesNeural"

audio_config = speechsdk.audio.AudioOutputConfig(filename="data/test_audio/azure_tts_output.wav")
synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

text = "ሽንኩርት ሁለት መቶ ብር ተመዝግቧል"
result = synthesizer.speak_text_async(text).get()

if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("Azure TTS saved to data/test_audio/azure_tts_output.wav")
else:
    print(f"Failed: {result.reason}")