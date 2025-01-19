from elevenlabs import voices
from dotenv import load_dotenv
import os

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

voices_list = voices(api_key=ELEVENLABS_API_KEY)

print("Available Voices:")
for voice in voices_list:
    print(f"Voice Name: {voice.name}, Voice ID: {voice.voice_id}")
