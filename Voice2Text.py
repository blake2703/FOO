import openai
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcript_mp3(file_path):
    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return response.text

if __name__ == "__main__":
    path = "voice2text.mp3"
    transcript = transcript_mp3(path)
    print(transcript)
