import os
from azure.cognitiveservices.speech import (
    SpeechConfig,
    AudioConfig,
    SpeechRecognizer,
    PronunciationAssessmentConfig,
    PronunciationAssessmentGranularity,
    PronunciationAssessmentGradingSystem
)
from azure.cognitiveservices.speech.audio import PushAudioInputStream
from dotenv import load_dotenv

load_dotenv()
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

async def analyze_pronunciation_with_azure(text: str, audio_data: bytes):
    """
    Azure Speech SDK를 사용하여 발음 평가를 수행하고 상세 결과를 반환.
    """
    # 1) PushAudioInputStream 생성
    audio_stream = PushAudioInputStream()

    # 2) PushAudioInputStream에 오디오 데이터 쓰기
    audio_stream.write(audio_data)
    audio_stream.close()

    # 3) SpeechConfig 및 AudioConfig 설정
    speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    audio_config = AudioConfig(stream=audio_stream)

    # 4) PronunciationAssessment 설정
    pronunciation_config = PronunciationAssessmentConfig(
        reference_text=text,
        grading_system=PronunciationAssessmentGradingSystem.HundredMark,
        granularity=PronunciationAssessmentGranularity.Phoneme
    )
    recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    pronunciation_config.apply_to(recognizer)

    # 5) 발음 평가
    result = recognizer.recognize_once()

    # 6) 상세 정보 추출 및 반환
    return {
        "result_properties": dict(result.properties) # 결과 속성을 딕셔너리로 변환
    }