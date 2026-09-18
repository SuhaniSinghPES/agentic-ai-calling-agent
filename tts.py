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


VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
MODEL_ID = "eleven_flash_v2_5"


def text_to_speech(text):

    audio = client.text_to_speech.convert(
        text=text,
        voice_id=VOICE_ID,
        model_id=MODEL_ID,
        output_format="mp3_44100_128"
    )

    return b"".join(audio)