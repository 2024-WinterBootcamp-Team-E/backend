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

def text_to_speech_data(text: str, voice_id: str) -> BytesIO:
    try:
        # ElevenLabs API 호출
        response = client.text_to_speech.convert(
            voice_id=voice_id,
            optimize_streaming_latency="0",
            output_format="mp3_22050_32",  # MP3 형식
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        audio_stream = BytesIO()
        for chunk in response:
            if chunk:
                audio_stream.write(chunk)
        audio_stream.seek(0)  # 스트림 시작 위치로 이동

        return audio_stream

    except Exception as e:
        raise RuntimeError(f"Error during TTS conversion: {str(e)}")