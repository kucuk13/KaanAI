from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play, save

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import api_key

def generate_voice_with_text(text, output_path):
    client = ElevenLabs(
      api_key=api_key.get("eleven-labs-api-key"),
    )

    voice = client.text_to_speech.convert(
        text=text,
        voice_id="ZF6FPAbjXT4488VcRRnw",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    #play(speech_response)
    save(voice, output_path)

def create_voices(text_parts):
    for i, part in enumerate(text_parts):
        output_filename = f"youtube/output/voices/output_part_{i+1}.mp3"
        generate_voice_with_text(part.strip(), output_filename)
