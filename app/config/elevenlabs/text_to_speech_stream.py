import asyncio
from fastapi import HTTPException
from elevenlabs import VoiceSettings, ElevenLabs
from dotenv import load_dotenv
import os

load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

async def generate_tts_audio_async(gpt_chunk: str, tts_id: str):
    try:
        response_generator = client.text_to_speech.convert(
            voice_id=tts_id,
            optimize_streaming_latency="0",
            output_format="mp3_22050_32",
            text=gpt_chunk,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: b"".join(response_generator))
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 변환 실패: {str(e)}")
