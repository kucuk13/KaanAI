from elevenlabs.client import ElevenLabs
from elevenlabs import save
from openai import OpenAI

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import api_key

eleven_labs_amelia = "ZF6FPAbjXT4488VcRRnw"
eleven_labs_adam = "wBXNqKUATyqu0RtYt25i"
chat_gpt_young_woman = "nova"
chat_gpt_middle_aged_woman = "alloy"
chat_gpt_middle_aged_man = "onyx"

def generate_voice_with_text_using_eleven_labs_api(text, output_path):
    client = ElevenLabs(
      api_key=api_key.get("eleven-labs-api-key"),
    )

    voice = client.text_to_speech.convert(
        text=text,
        voice_id=eleven_labs_adam,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    save(voice, output_path)

def generate_voice_with_text_using_chatgpt_api(text, output_filename):
    voice = ""
    client = OpenAI(api_key = api_key.get("chat-gpt-api-key"))
    
    if "X:" in text:
        voice = chat_gpt_young_woman
    else:
        voice = chat_gpt_middle_aged_man
    
    text = text.replace("X:", "")
    text = text.replace("O:", "")
    
    try:
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice=voice,
            input=text
        ) as response:
            temp_file = output_filename
            with open(temp_file, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
    except Exception as e:
        print(f".Error: {e}")

def create_voices(text_parts, is_short_video):
    for i, part in enumerate(text_parts):
        output_filename = f"youtube/output/voices/{i+1}.mp3"
        if is_short_video:
            generate_voice_with_text_using_chatgpt_api(part.strip(), output_filename)
        else:
            generate_voice_with_text_using_eleven_labs_api(part.strip(), output_filename)
