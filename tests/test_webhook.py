import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs


load_dotenv()


api_key = os.getenv("ELEVENLABS_API_KEY")

if not api_key:
    raise RuntimeError(
        "ELEVENLABS_API_KEY is not configured."
    )


client = ElevenLabs(
    api_key=api_key
)


audio_path = "test_voice.mp3"


with open(audio_path, "rb") as audio_file:

    result = client.speech_to_text.convert(
        file=audio_file,
        model_id="scribe_v2",
        webhook=True
    )


print()
print("================================")
print("TRANSCRIPTION REQUEST STARTED")
print("================================")
print("Request ID:", result.request_id)
print("================================")
print()