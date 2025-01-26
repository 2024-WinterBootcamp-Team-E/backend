import asyncio
from fastapi import HTTPException
from io import BytesIO
from elevenlabs import VoiceSettings, ElevenLabs
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# ElevenLabs API Key
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# ElevenLabs 클라이언트 초기화
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
#바이트 아이오 타입으로 보내고 청크로 sse로 보낸다고 해도 어짜피 모아져 있는거를 나눠서 보내는거고 스트리밍 형식으로 하면
#그걸 안모으고 나오자마자 바로보내는 형식
async def generate_tts_audio_async(gpt_chunk: str, tts_id: str):
    """
    GPT 청크를 받아 TTS 데이터를 비동기로 스트리밍합니다.
    """
    try:
        # ElevenLabs API 호출 (스트리밍 지원)
        response = client.text_to_speech.convert(
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

        # 응답을 청크 단위로 비동기적으로 반환
        for chunk in response:
            if chunk:  # 빈 청크 무시
                await asyncio.sleep(0)  # 비동기 컨텍스트 유지
                yield chunk

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 변환 실패: {str(e)}")
