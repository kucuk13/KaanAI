from openai import OpenAI
import api_key

client = OpenAI(api_key = api_key.get("chat-gpt-api-key"))

dialogue = [
    "Hey. how are you?",
    "I'm good. Thanks! How about you?"
]

for i, text in enumerate(dialogue):
    voice = "alloy" if i % 2 == 0 else "nova" #onyx(middle-aged man), alloy(middle-aged woman), nova(young woman)
    try:
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice=voice,
            input=text
        ) as response:
            temp_file = f"{i+1}.mp3"
            with open(temp_file, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
    except Exception as e:
        print(f"{i+1}. got error: {e}")
