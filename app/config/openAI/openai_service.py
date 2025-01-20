import asyncio
import io
import json
import os
import openai
from fastapi import HTTPException, UploadFile
from dotenv import load_dotenv
from app.models import Feedback




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
    # 시스템 역할 설정
    system_message = {
        "role": "system",
        "content": (
            "You are a pronunciation expert providing detailed feedback. "
            "Identify problematic words, explain issues clearly, and suggest improvements. "
            "Respond in a conversational tone without unnecessary compliments."
        )
    }

    # 메시지 초기화
    messages = [system_message]  # 시스템 메시지 추가
    messages.append({
        "role": "user",
        "content": (
            f"사용자가 발음한 문장 {text}\n"
            f"음절 피드백 {words}\n\n"
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
            messages=messages,
            stream=True
        )
        # 비동기 제너레이터로 응답 처리
        async for chunk in response:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    yield delta['content']



    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate GPT feedback: {str(e)}"
        )

async def sse_generator_wrapper(
    generator,  # get_pronunciation_feedback에서 받은 async generator
    user_id: int,
    sentence_id: int,
    db,
    scores: dict
):
    """
    generator로부터 chunk를 받으면서 SSE 형식("data: ...\n\n")으로 클라이언트에게 전송한다.
    스트리밍이 끝난 뒤 누적된 전체 피드백을 DB에 저장한다.
    """
    feedback_accumulator = []
    try:
        async for chunk in generator:
            feedback_accumulator.append(chunk)
            # SSE 포맷: data: {message}\n\n
            yield f"data: {chunk}\n\n"
            # 너무 빠르게 전송 시 버퍼링 문제가 생길 수 있어 잠시 대기
            await asyncio.sleep(0.01)

        # 모든 스트리밍이 끝나면 전체 피드백을 합친다.
        feedback = "".join(feedback_accumulator)

        # DB에 저장 로직
        # 예: Feedback 테이블에 accuracy_score, fluency_score 등 저장
        # 이미 Feedback model이 있다고 가정
        feedback_entry = db.query(Feedback).filter_by(user_id=user_id, sentence_id=sentence_id).first()
        if not feedback_entry:
            feedback_entry = Feedback(user_id=user_id, sentence_id=sentence_id)
            db.add(feedback_entry)

        feedback_entry.accuracy_score = scores["AccuracyScore"]
        feedback_entry.fluency_score = scores["FluencyScore"]
        feedback_entry.completeness_score = scores["CompletenessScore"]
        feedback_entry.pron_score = scores["PronScore"]
        feedback_entry.pronunciation_feedback = feedback
        db.commit()

    except Exception as e:
        # 스트리밍 중 오류
        print(f"[ERROR] During streaming: {e}")
        # SSE 스트리밍 도중 예외를 발생하면 연결이 강제로 끊길 수 있음
        # 필요하다면 아래처럼 특정 SSE 메시지를 보낸 뒤 종료할 수도 있음
        raise HTTPException(status_code=500, detail=f"스트리밍 중 오류가 발생했습니다: {str(e)}")