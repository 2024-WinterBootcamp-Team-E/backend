from fastapi import FastAPI, UploadFile, HTTPException
from botocore.exceptions import BotoCoreError, ClientError
import aioboto3
import uuid
import os

app = FastAPI()

# AWS S3 설정
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
VALID_DIRECTORIES = ["travel", "business", "daily", "movie"]


async def upload_audio(file: UploadFile, category: str):
    if category not in VALID_DIRECTORIES:
        raise HTTPException(status_code=400, detail="유효하지 않은 카테고리입니다.")
    if file.filename.split(".")[-1].lower() not in ["wav", "mp3"]:
        raise HTTPException(status_code=400, detail="WAV 또는 MP3 파일만 업로드 가능합니다.")

    unique_filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    s3_key = f"{category}/{unique_filename}"

    session = aioboto3.Session()
    async with session.client(
            "s3",
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=AWS_REGION,
    ) as s3_client:
        try:
            await s3_client.upload_fileobj(file.file, BUCKET_NAME, s3_key)
        except (BotoCoreError, ClientError) as e:
            raise HTTPException(status_code=500, detail=f"S3 업로드 실패: {str(e)}")

    file_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
    return file_url
