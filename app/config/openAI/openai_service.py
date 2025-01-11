import openai
from fastapi import HTTPException
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# Wisper
def transcribe_audio(file) -> str:
    """
    OpenAI Whisper API를 사용해 음성을 텍스트로 변환합니다.
    :param file: 업로드된 음성 파일
    :return: 변환된 텍스트
    """
    try:
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=file
        )
        return response["text"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {str(e)}")

# gpt
def get_gpt_response(prompt: str, subject: str, messages: list) -> str:
    """
    OpenAI GPT를 사용해 대화 응답을 생성합니다.
    :param prompt: 사용자의 입력 텍스트
    :param subject: 채팅방 주제
    :param messages: 이전 대화 히스토리
    :return: GPT 응답 텍스트
    """
    # GPT 메시지 형식에 주제를 포함
    messages.append({"role": "user", "content": f"[주제: {subject}]\n{prompt}"})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT 응답 생성 실패: {str(e)}")
