import os
import openai

'''
alloy : Conversational and clear
echo : Deep and calm
fable : Expressive and story-like
onyx : Crisp and assertive
nova : Bright and friendly
shimmer : Airy and gentle
'''

def text_to_speech_from_file(input_path="T2V.txt", voice="alloy", output_path="output.mp3"):
    """
    Reads text from a file and uses OpenAI's TTS API to generate an MP3 audio file.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")

    openai.api_key = api_key

    try:
        with open(input_path, "r", encoding="utf-8") as file:
            text = file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file {input_path} not found.")
    except Exception as e:
        raise RuntimeError(f"Failed to read input file: {e}")

    try:
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"MP3 file created at {output_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to generate speech: {e}")

if __name__ == "__main__":
    text_to_speech_from_file()
