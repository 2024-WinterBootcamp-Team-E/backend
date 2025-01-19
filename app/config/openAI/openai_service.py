import io
import json
import os

from fastapi import HTTPException, UploadFile
from dotenv import load_dotenv

import openai
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
async def get_pronunciation_feedback(azure_response: dict) -> str:
    # 시스템 역할 설정
    system_message = {
        "role": "system",
        "content": (
            "You are a pronunciation expert providing detailed feedback. "
            "Identify problematic words, explain issues clearly, and suggest improvements. "
            "Respond in a conversational tone without unnecessary compliments."
        )
    }

    # Azure 응답 데이터를 메시지로 변환
    azure_response_str = "\n".join(
        f"{key}: {value}" for key, value in azure_response.items()
    )

    # 메시지 초기화
    messages = [system_message]  # 시스템 메시지 추가
    messages.append({
        "role": "user",
        "content": (
            f"{azure_response_str}\n\n"
            "이 데이터를 바탕으로, 피드백을 작성해 주세요:\n"
            "1. 발음에서 문제가 있었던 단어를 찾아주세요.\n"
            "2. 문제가 되는 발음의 원인은 구체적으로 설명해 주고 개선방향을 알려주세요.\n"
            "3. 문제가 없거나 잘한 부분은 언급하지 말아주세요.\n"
            "출력 형식은 대화체로 작성해 주세요. 응원, 인사말 같은 불필요한 말은 빼고 30단어 내외로 작성해 주세요."
        )
    })

    try:
        # 비동기 OpenAI GPT 호출
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate GPT feedback: {str(e)}"
        )
