import io
import openai
from fastapi import HTTPException, UploadFile, Depends
from dotenv import load_dotenv
import os
import json
from pymongo.database import Database
from app.database.session import get_mongo_db
from fastapi import HTTPException, UploadFile
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

async def transcribe_audio(file_content_io: io.BytesIO,filename:str) -> str:
    file_content_io.name= filename
    try:
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=file_content_io,
        )
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {str(e)}")

async def get_gpt_response_limited(chat_id: int, prompt: str, mdb) -> str:
    collection = mdb["chats"]
    result = collection.find_one({"chat_id": chat_id}, {"messages": {"$slice": -6}})
    system_message = {
        "role": "system",
        "content": (
            "You are an AI assistant that provides concise and natural responses. "
            "Keep answers under 30 words, include follow-up questions, and maintain an engaging tone."
        )
    }
    conversation = [system_message]

    if result and "messages" in result and result["messages"]:
        for message in result["messages"]:
            if isinstance(message, dict):
                conversation.append({
                    "role": message.get("role", "user"),
                    "content": message.get("content", "")
                })

    conversation.append({
        "role": "user",
        "content": prompt
    })

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation,
            stream=True,
        )

        for chunk in response:
            if "choices" in chunk and chunk["choices"]:
                delta = chunk["choices"][0]["delta"]
                if "content" in delta and delta["content"]:
                    yield delta["content"]

    except Exception as e:
        yield f"data: {json.dumps({'step': 'error', 'message': f'GPT 응답 생성 실패: {str(e)}'})}\n\n"
async def get_grammar_feedback(prompt: str) -> str:
    system_message = {
        "role": "system",
        "content": "You are a grammar expert providing concise feedback to improve writing quality."
    }

    messages = [
        system_message,
        {"role": "user", "content": f"Please provide grammar feedback for the following text: {prompt}"}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        return response.choices[0].message.content
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
