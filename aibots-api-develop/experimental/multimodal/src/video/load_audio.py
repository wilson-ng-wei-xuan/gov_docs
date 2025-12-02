
from transformers import pipeline

def transcribe(file_path):
    pipe = pipeline("automatic-speech-recognition", model="openai/whisper-small")
    transcription = pipe(file_path)
    return transcription