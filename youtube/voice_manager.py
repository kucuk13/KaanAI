from elevenlabs.client import ElevenLabs
from elevenlabs import save
from openai import OpenAI
from pydub import AudioSegment, silence
from stable_whisper import load_model
from constants import whisper_model
import sort_manager
import re
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import api_key

eleven_labs_amelia = "ZF6FPAbjXT4488VcRRnw"
eleven_labs_adam = "wBXNqKUATyqu0RtYt25i"

#chatgpt female voices 
chatgpt_alloy = "alloy" #standard, middle-aged*
chatgpt_fable = "fable" #standard, middle-aged
chatgpt_nova = "nova" #cheerful, young**
chatgpt_sage = "sage" #cheerful, young*
chatgpt_shimmer = "shimmer" #cheerful, middle-aged

#chatgpt male voices 
chatgpt_ash = "ash" #standard, young
chatgpt_echo = "echo" #soft, young*
chatgpt_onyx = "onyx" #standard, middle-aged**

def generate_voices_using_chatgpt_api(text_parts, voice1, voice2, voice3, voice4):
    for i, text in enumerate(text_parts):
        output_filename = f"youtube/output/voices/{i+1}.mp3"
        if "1:" in text:
            text = text.replace("1:", "")
            generate_voice_using_chatgpt_api(text.strip(), voice1, output_filename)
        elif "2:" in text:
            text = text.replace("2:", "")
            generate_voice_using_chatgpt_api(text.strip(), voice2, output_filename)
        elif "3:" in text:
            text = text.replace("3:", "")
            generate_voice_using_chatgpt_api(text.strip(), voice3, output_filename)
        else:
            text = text.replace("4:", "")
            generate_voice_using_chatgpt_api(text.strip(), voice4, output_filename)

def generate_voice_using_chatgpt_api(text, voice, output_filename):
    client = OpenAI(api_key = api_key.get("chat-gpt-api-key"))
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

def generate_voices_using_eleven_labs_api(text_parts, voice1):
    for i, text in enumerate(text_parts):
        output_filename = f"youtube/output/voices/{i+1}.mp3"
        generate_voice_using_eleven_labs_api(text.strip(), voice1, output_filename)

def generate_voice_using_eleven_labs_api(text, voice1, output_path):
    client = ElevenLabs(
      api_key=api_key.get("eleven-labs-api-key"),
    )

    voice = client.text_to_speech.convert(
        text=text,
        voice_id=voice1,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    save(voice, output_path)

def clean_voice_file(input_file_path, output_file_path):
    voice = AudioSegment.from_mp3(input_file_path)

    non_silence_segments = silence.split_on_silence(
        voice,
        min_silence_len=700,   # Minimum silence length (in ms) to consider as silence
        silence_thresh=-40,     # Silence threshold (in dB)
        keep_silence=100        # Keep 100ms of silence at edges
    )
    
    if not non_silence_segments:
        print(f"Warning: No audible sound found in {input_file_path}.")
        return
    
    output_voice = AudioSegment.empty()
    for segment in non_silence_segments:
        output_voice += segment
    
    output_voice.export(output_file_path, format="mp3")
    print(f"Completed: {output_file_path}")

def clean_voice_files():
    input_path_temp = os.path.abspath("youtube/output/voices")
    output_path_temp = os.path.abspath("youtube/output/audios")
    
    voice_files = sorted(
        [f for f in os.listdir(input_path_temp) if f.endswith(".mp3")],
        key=sort_manager.numerical_sort
    )

    for file_name in voice_files:
        input_path = os.path.join(input_path_temp, file_name)
        output_path = os.path.join(output_path_temp, f"{file_name}")
        clean_voice_file(input_path, output_path)

def load_sentences(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())

def find_sentence_timing(target_words, segments):
    """
    Find the start and end timestamp for a sequence of words.
    Returns (start_time, end_time) or (None, None) if not found.
    """
    target_len = len(target_words)

    for seg in segments:
        words = seg.words
        normalized_words = [normalize(w.word) for w in words]

        for i in range(len(normalized_words) - target_len + 1):
            # match continuous sequence
            if normalized_words[i:i+target_len] == target_words:
                start_time = words[i].start
                end_time = words[i + target_len - 1].end
                return start_time, end_time

    return None, None

def split_voices(input_script_file, input_voice_file, output_path):
    sentences = load_sentences(input_script_file)
    os.makedirs(output_path, exist_ok=True)

    print("Loading model...")
    model = load_model(whisper_model.small.value)

    print("Transcribing...")
    result = model.transcribe(input_voice_file, regroup=False)

    print("Processing timings...")
    sentence_timings = []
    for sentence in sentences:
        normalized_words = [normalize(w) for w in sentence.split()]
        start, end = find_sentence_timing(normalized_words, result.segments)
        sentence_timings.append((sentence, start, end))

    print("Extracting audio segments...")
    audio = AudioSegment.from_file(input_voice_file)

    for i, (text, start, end) in enumerate(sentence_timings, start=1):
        if start is None or end is None:
            print(f"Skipped (not found): {text}")
            continue

        out_file = os.path.join(output_path, f"{i}.mp3")
        audio[int(start * 1000):int(end * 1000)].export(out_file, format="mp3")
        print(f"Saved: {out_file}")

    print("Done.")
