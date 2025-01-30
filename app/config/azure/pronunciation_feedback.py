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

# 발음 평가
async def analyze_pronunciation_with_azure(text: str, audio_data: bytes):
    audio_stream = PushAudioInputStream()
    audio_stream.write(audio_data)

    audio_stream.close()
    speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.set_property(PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")
    speech_config.set_property(PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "5000")
    audio_config = AudioConfig(stream=audio_stream)

    pronunciation_config = PronunciationAssessmentConfig(
        reference_text=text,
        grading_system=PronunciationAssessmentGradingSystem.HundredMark,
        granularity=PronunciationAssessmentGranularity.Phoneme,
    )

    pronunciation_config.enable_prosody_assessment()
    recognizer = SpeechRecognizer(speech_config=speech_config, language='en-US', audio_config=audio_config)
    pronunciation_config.apply_to(recognizer)
    result = recognizer.recognize_once()

    pronunciation_assessment_result_json = result.properties.get(
        PropertyId.SpeechServiceResponse_JsonResult)
    # print(f"[LOG] JSON Result: {pronunciation_assessment_result_json}")
    return json.loads(pronunciation_assessment_result_json)