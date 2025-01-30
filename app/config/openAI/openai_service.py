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
            language="en"
        )
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {str(e)}")

async def get_gpt_response_limited(chat_id: int, prompt: str, title:str, country:str, mdb) -> str:
    collection = mdb["chats"]
    result = collection.find_one({"chat_id": chat_id}, {"messages": {"$slice": -8}})
    if country == '미국':
        country_code  = 'US'
    else:
        country_code  = "UK"
    system_message = {
        "role": "system",
        "content": (
            "You are an English conversational assistant.\n"
            f"Current Subject: {title}\n"
            f"Country: {country_code} (either US for American English or UK for British English)\n"
            "Please proceed according to the description below.\n"
            "1. **Language Variant:** Use vocabulary and phrasing appropriate for the specified country. For example, use 'trousers' for UK and 'pants' for US.\n"
            "2. **Consistency:** Maintain the chosen English variant consistently throughout the conversation.\n"
            "3. **Response Guidelines:**\n"
            "   - Keep answers concise, under 30 words.\n"
            "   - Include relevant follow-up questions to keep the conversation flowing naturally.\n"
            "   - Maintain an engaging and friendly tone.\n"
            "4. **Handling No Differences:** If there are no significant vocabulary differences, use standard English appropriate for the specified country.\n"
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
            model="gpt-4o-mini",
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

async def get_grammar_feedback(prompt: str, country:str) -> str:
    if country == '미국':
        country = 'US'
    else:
        country = 'UK'
    system_message = {
        "role": "system",
        "content": (
            "당신은 문법 전문가로서 사용자의 글쓰기 품질을 향상시키기 위해 간결한 피드백을 제공합니다.\n"
            "아래 지시사항을 준수하여 한국어로 답변해주세요.\n"
            "1. 기본적인 영어 문법 피드백뿐만 아니라 지정된 국가({country})에 맞춰 제안을 조정하세요.\n"
            "2. 문법과 단어 선택이 해당 국가의 영어에 적합한지 확인하세요.\n"
            "   예를 들어, 영국식 영어에서는 'trousers'를, 미국식 영어에서는 'pants'를 사용하거나,\n"
            "   영국식 영어에서는 'trainers'를, 미국식 영어에서는 'sneakers'를 사용하는 식입니다.\n"
            "3. 피드백은 명확하고 실행 가능하며 40단어 이내로 유지하세요.\n"
            "4. 사용자가 말한 문장에서 문법이 잘못된 부분을 구체적으로 지적하고, 개선 방법을 제안하세요. 불필요한 칭찬이나 인사는 포함하지 않습니다.\n"
            "5. 피드백은 다음 형식을 따릅니다:\n"
            "   \"[단어/문장]에서 [오류 유형]을 발견했습니다. [개선 방법]\"\n"
            "   예시 1: \"미국에서는 'trousers' 보다는 'pants'를 사용합니다.\"\n"
            "   예시 2: \"'to 10 years' 보다는 'for 10 years'가 맞습니다. 기간을 나타낼 때 'for'를 사용하세요.\"\n"
        ).format(country=country)
    }
    messages = [
        system_message,
        {"role": "user", "content": f"Please provide grammar feedback for the following text: {prompt}"}
    ]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문법 피드백 생성 실패: {str(e)}")

async def get_pronunciation_feedback(words: dict, text:str) -> str:
    system_message = {
        "role": "system",
        "content": (
            "당신은 영어 발음 교정 전문가입니다.\n"
            "아래 지시사항을 준수하여 한국어로 답변해주세요.\n"
            "1. 항상 존댓말을 사용하여 일관된 말투를 유지합니다."
            "2. 문제가 있는 단어만 지적합니다.\n"
            "3. 잘한 부분이나 불필요한 인사는 언급하지 않습니다..\n"
            "4. 답변은 총 180자 이내로 작성합니다.\n"
            "5. 문제가 있는 단어가 많아 답변이 길어질 경우 몇몇 문제만 피드백합니다.\n"
            "\noutput: 발음 오류 원인과 개선 방법을 간단하게 설명"
        )
    }
    messages = [system_message]

    messages.append({
        "role": "user",
        "content": (
            f"사용자가 발음한 문장: {text}\n"
            f"발음 피드백 데이터:\n```\n{words['processed']}\n```"
        )
    })
    print(f"[[[processed]]] : {words['processed']}")
    try:
        # 비동기 OpenAI GPT 호출
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
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
    generator,
    user_id: int,
    sentence_id: int,
    db,
    scores: dict,
    preprocessed
):
    """
    generator로부터 chunk를 받으면서 SSE 형식으로 클라이언트에게 전송
    스트리밍이 끝난 뒤 누적된 전체 피드백을 DB에 저장
    """
    yield f"pronscore: {scores['PronScore']}\n\n"
    feedback_accumulator = []
    try:
        async for chunk in generator:
            feedback_accumulator.append(chunk)
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.005)
        # 모든 스트리밍이 끝나면 전체 피드백을 합친다.
        feedback = "".join(feedback_accumulator)

        json_str = json.dumps(preprocessed, ensure_ascii=False)
        yield f"result:{json_str}\n\n"


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
        print(f"[ERROR] During streaming: {e}")
        raise HTTPException(status_code=500, detail=f"스트리밍 중 오류가 발생했습니다: {str(e)}")