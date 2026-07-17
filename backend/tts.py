import os
import uuid
import azure.cognitiveservices.speech as speechsdk
from tenacity import retry, stop_after_attempt, wait_exponential

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
def synthesize_speech(text: str, output_dir: str = "data/outgoing_voice") -> str:
    """Generate Amharic speech audio for the given text. Returns the path to the saved .wav file, or None on failure."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}.wav"
    output_path = os.path.join(output_dir, filename)

    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = "am-ET-MekdesNeural"

    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return output_path
    else:
        raise RuntimeError(f"TTS failed: {result.reason}")
