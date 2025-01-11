import io

import openai
from fastapi import HTTPException,UploadFile
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

# Whisper (STT)
def transcribe_audio(file: UploadFile) -> str:
    try:
        # 파일 포인터를 처음으로 리셋
        file.file.seek(0)

        # SpooledTemporaryFile을 BytesIO로 변환
        file_content = io.BytesIO(file.file.read())
        file_content.name = file.filename  # 파일 이름 설정 (필수)

        # Whisper API 호출
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=file_content  # BytesIO 객체 전달
        )

        # 변환된 텍스트 반환
        return response["text"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {str(e)}")

# GPT 대화 응답 생성
def get_gpt_response(prompt: str, messages: list) -> str:
    messages.append({"role": "user", "content": prompt})
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT 응답 생성 실패: {str(e)}")