FROM python:3.10

WORKDIR /app
RUN pip install --upgrade pip
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# PYTHONPATH 설정
ENV PYTHONPATH=/app

CMD ["sh", "-c", "PYTHONPATH=/app uvicorn app.main:app --host 0.0.0.0 --port 8000"]