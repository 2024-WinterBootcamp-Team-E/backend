import io
import openai
from fastapi import HTTPException,UploadFile
from dotenv import load_dotenv

import os


load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def transcribe_audio(file: UploadFile) -> str:
    try:
        file.file.seek(0)
        file_content = io.BytesIO(file.file.read())
        file_content.name = file.filename  # 파일 이름 설정 (필수)
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=file_content
        )

        # 변환된 텍스트 반환
        return response["text"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {str(e)}")

def get_gpt_response_limited(prompt: str, messages: list) -> str:
    messages.append({
        "role": "user",
        "content": "Assume the user is speaking English.\n"
                   f"Respond in 30 words or less with natural, concise, and relevant answers that include a follow-up question or invitation to continue the conversation, ensuring the dialogue stays engaging and interactive. Here is the prompt: {prompt}"
    })
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT 응답 생성 실패: {str(e)}")

def get_grammar_feedback(prompt: str, messages: list) -> str:
    messages.append({
        "role": "user",
        "content": "다음 문장을 분석하고 아래 조건에 따라 문법적으로 오류가 있는 부분을 모두 찾아줘\n"
                    "모든 문법적인 오류를 찾고, 왜 오류인지 설명해줘\n"
                    "올바른 표현 방법을 알려줘.\n"
                    "불필요한 말은 하지 말아줘\n"
                    f"대화체로 설명해 주세요 또한 설명을 한국어로 친절하게 작성해 주세요: {prompt}"
    })
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문법 피드백 생성 실패: {str(e)}")

async def get_pronunciation_feedback(azure_response: dict) -> str:
    azure_response_str = "\n".join(
        f"{key}: {value}" for key, value in azure_response.items()
    )

    messages = [
        {
            "role": "user",
            "content": (
                f"{azure_response_str}\n\n"
                "이 데이터를 바탕으로, 피드백을 작성해 주세요:\n"
                "1. 발음에서 문제가 있었던 단어를 찾아주세요.\n"
                "2. 문제가 되는 발음의 원인은 구체적으로 설명해 주고 개선방향을 알려주세요.\n"
                "3. 문제가 없거나 잘한 부분은 언급하지 말아주세요\n"
                "출력 형식은 대화체로 작성해 주세요. 응원, 인사말같은 불필요한 말은 빼고 30단어 내외로 작성해 주세요.\n"


            )
        }
    ]

    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=messages
        )
        return response["choices"][0]["message"]["content"]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate GPT feedback: {str(e)}"
        )
