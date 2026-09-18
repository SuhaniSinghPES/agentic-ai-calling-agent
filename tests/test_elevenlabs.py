import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")

if not api_key:
    raise RuntimeError("ELEVENLABS_API_KEY is not configured.")

client = ElevenLabs(
    api_key=api_key
)

audio = client.text_to_speech.convert(
    text="Hello! This is the AI Calling Agent speaking through ElevenLabs.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_flash_v2_5",
    output_format="mp3_44100_128"
)

with open("test_voice.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)

print("SUCCESS: ElevenLabs generated test_voice.mp3")