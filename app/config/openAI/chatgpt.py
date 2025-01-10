import os
import openai
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

# .env 파일 로드
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.post("/generate")
async def generate_text(request: Request):
    data = await request.json()
    user_input = data.get("message", "")

    if not user_input:
        return {"error": "Message is required"}

    # OpenAI API 호출
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=user_input,
        max_tokens=150,
        temperature=0.7,
        stream=True,  # SSE 지원
    )

    # SSE 스트리밍 생성기
    def sse_generator():
        for chunk in response:
            if "choices" in chunk:
                yield f"data: {chunk['choices'][0]['text']}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
