import io
import openai
from fastapi import HTTPException, UploadFile, Depends
from dotenv import load_dotenv
import os
import json
from pymongo.database import Database
from app.database.session import get_mongo_db

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


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

def get_gpt_response_limited(chat_id: int, prompt: str, messages: list, mdb) -> str:
    collection = mdb["chats"]  # 'chats' 콜렉션으로 변경
    result = collection.find_one({"chat_id": chat_id}, {"messages": {"$slice": -6}})

    if result and "messages" in result and result["messages"]:
        for message in result["messages"]:
            if isinstance(message, dict):  # 데이터 검증
                messages.append({
                    "role": message.get("role", "user"),
                    "content": message.get("content", "")
                })
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

async def get_pronunciation_feedback(words: list, text:str) -> str:
    words_json_str = json.dumps(words, ensure_ascii=False, indent=0)

    # 2) 메시지 구성
    #  - 첫 번째(system): ChatGPT에게 규칙 및 평가 요약 제공
    #  - 두 번째(user): 발음 피드백 요청
    system_message = (
        "당신은 사용자의 발음 상태를 분석하는 전문가입니다.\n"
        f"사용자가 발음한 문장: '{text}'\n\n"
        "아래는 단어의 음절에 대한 발음 평가 데이터입니다:\n"
        f"{words_json_str}\n\n"
        "당신의 목표:\n"
        "1. 잘못 발음된 음절들을 찾아서 구체적으로 지적\n"
        "3. 개선 방향을 알려주되, 응원/인사말은 빼고\n"
        "4. 전체 30단어 내외로 짧게, 간결한 문장으로 작성\n"
    )

    # 2) user 메시지
    #    - 사용자가 발음 피드백을 부탁한다는 상황을 설정
    user_message = (
        "제 발음 평가 결과를 토대로, 음절 단위 발음 피드백을 간략히 알려주세요."
    )
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
    # 3) OpenAI ChatCompletion 호출
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response["choices"][0]["message"]["content"]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate GPT feedback: {str(e)}"
        )
