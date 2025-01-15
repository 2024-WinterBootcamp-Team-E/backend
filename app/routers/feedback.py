from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.config.azure.pronunciation_feedback import analyze_pronunciation_with_azure
from app.services.feedback_service import create_feedback_from_azure_response
from app.models.sentence import Sentence
from app.config.openAI.openai_service import get_pronunciation_feedback
from app.models.feedback import Feedback

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"]
)

@router.post("/{user_id}/{sentence_id}", summary="발음 분석", description="Azure Speech SDK를 이용해 발음 평가 결과 반환 및 데이터 저장")
async def analyze_pronunciation_endpoint(
        user_id: int,
        sentence_id: int,
        audio_file: UploadFile,
        db: Session = Depends(get_db),
):
    try:
        # `sentence_id`로 문장을 조회하여 content 가져오기
        sentence_entry = db.query(Sentence).filter_by(sentence_id=sentence_id, is_deleted=False).first()
        if not sentence_entry:
            raise HTTPException(status_code=404, detail="해당 문장을 찾을 수 없습니다.")

        # `sentence_id`에 해당하는 문장의 content를 발음 텍스트로 사용
        text = sentence_entry.content
        print(f"[LOG] Sentence Content: {text}")

        # 업로드된 오디오 파일 읽기
        audio_data = await audio_file.read()

        # Azure Speech SDK로 발음 분석 수행
        azure_result = await analyze_pronunciation_with_azure(text, audio_data)
        print(f"[LOG] Azure Result: {azure_result}")

        # GPT를 이용해 추가 피드백 생성
        gpt_result = await get_pronunciation_feedback(azure_result)

        # 결과를 데이터베이스에 저장
        feedback_entry = db.query(Feedback).filter_by(user_id=user_id, sentence_id=sentence_id).first()
        if not feedback_entry:
            # 기존 항목이 없으면 새로 생성
            feedback_entry = Feedback(user_id=user_id, sentence_id=sentence_id)
            db.add(feedback_entry)

        # 발음 피드백 업데이트
        feedback_entry.pronunciation_feedback = gpt_result
        db.commit()

        return {
            "sentence_content": text,
            "gpt_result": gpt_result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="발음 평가 중 오류가 발생했습니다.")
