from http.client import HTTPException

from fastapi.responses import StreamingResponse
from elevenlabs import VoiceSettings, ElevenLabs
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# ElevenLabs API Key
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# ElevenLabs 클라이언트 초기화
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def text_to_speech_data(text: str, voice_id: str) -> StreamingResponse:
    try:
        response = client.text_to_speech.convert_streaming(
            voice_id=voice_id,
            text=text,
            output_format="mp3_22050_32",
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            ),
        )

        async def audio_stream():
            for chunk in response:
                if chunk:
                    yield chunk

        return StreamingResponse(audio_stream(), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 변환 실패: {str(e)}")