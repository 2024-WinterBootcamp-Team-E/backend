import os
from azure.cognitiveservices.speech import (
    SpeechConfig,
    AudioConfig,
    SpeechRecognizer,
    PronunciationAssessmentConfig,
    PronunciationAssessmentGranularity,
    PronunciationAssessmentGradingSystem,
    PropertyId
)
from azure.cognitiveservices.speech.audio import PushAudioInputStream
from dotenv import load_dotenv
import json

load_dotenv()
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

async def analyze_pronunciation_with_azure(text: str, audio_data: bytes):
    # 1) PushAudioInputStream 생성
    audio_stream = PushAudioInputStream()

    # 2) PushAudioInputStream에 오디오 데이터 쓰기
    audio_stream.write(audio_data)
    audio_stream.close()

    # 3) SpeechConfig 및 AudioConfig 설정
    speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.set_property(PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")
    speech_config.set_property(PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "5000")

    audio_config = AudioConfig(stream=audio_stream)

    # 4) PronunciationAssessment 설정
    pronunciation_config = PronunciationAssessmentConfig(
        reference_text=text,
        grading_system=PronunciationAssessmentGradingSystem.HundredMark,
        granularity=PronunciationAssessmentGranularity.Phoneme,
    #    enable_miscue = True
    )
    pronunciation_config.enable_prosody_assessment()
    recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    pronunciation_config.apply_to(recognizer)

    # 5) 발음 평가
    result = recognizer.recognize_once()
    pronunciation_assessment_result_json = result.properties.get(
        PropertyId.SpeechServiceResponse_JsonResult)
    print(f"[LOG] JSON Result: {pronunciation_assessment_result_json}")
    # 6) 상세 정보 추출 및 반환
    return json.loads(pronunciation_assessment_result_json)