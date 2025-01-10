import whisper

# Whisper STT 처리
def transcribe_audio(file):
    model = whisper.load_model("base")
    result = model.transcribe(file)
    return result["text"]
