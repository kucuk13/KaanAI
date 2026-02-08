from elevenlabs.client import ElevenLabs
from elevenlabs import save
from openai import OpenAI
from pydub import AudioSegment, silence
from stable_whisper import load_model
from difflib import SequenceMatcher
from constants import whisper_model
import sort_manager
import file_manager
import re
import os
import sys
from dotenv import load_dotenv

load_dotenv()

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
    client = OpenAI(api_key = os.getenv("CHAT_GPT_API_KEY"))
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
      api_key=os.getenv("ELEVENLABS_API_KEY"),
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

def normalize(text: str) -> str:
    txt = re.sub(r"[^\w\sşçöüğİı]", "", txt)
    txt = re.sub(r"\s+", " ", txt)
    txt = re.sub(r"[^a-z0-9]+", "", text.lower())
    return txt.strip()

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def get_words(segments):
    words = []
    for seg in segments:
        if "words" in seg and seg["words"] is not None:
            for w in seg["words"]:
                words.append(w)
    return words

def find_last_word_end(sentence, words):
    sent = normalize(sentence)
    sent_tokens = sent.split()

    last_time = None
    word_idx = 0

    for w in words:
        w_norm = normalize(w["word"])

        if w_norm == sent_tokens[word_idx]:
            last_time = w["end"]
            word_idx += 1

            if word_idx == len(sent_tokens):
                break

    return last_time

def split_voices(input_script_file, input_voice_file, output_path):
    with open(input_script_file, "r", encoding="utf-8") as f:
        sentences = [s.strip() for s in f if s.strip()]

    os.makedirs(output_path, exist_ok=True)

    print("Loading Whisper...")
    model = load_model("medium")

    print("Transcribing...")
    result = model.transcribe(
        input_voice_file,
        word_timestamps=True,
        regroup=False
    )

    words = []
    for seg in result.segments:
        if seg.words:
            words.extend(seg["words"])

    def norm(t):
        t = t.lower()
        t = re.sub(r"[^\w\sçğıöüşİı]", "", t)
        return re.sub(r"\s+", " ", t).strip()

    cut_points = []
    for sent in sentences:
        tokens = norm(sent).split()
        idx = 0
        last_time = None

        for w in words:
            if norm(w["word"]) == tokens[idx]:
                last_time = w["end"]
                idx += 1
                if idx == len(tokens):
                    break

        if last_time is None:
            print("NOT FOUND:", sent)
            last_time = (cut_points[-1] + 0.3) if cut_points else 0.3

        cut_points.append(last_time)

    audio = AudioSegment.from_file(input_voice_file)
    cut_points[-1] = audio.duration_seconds

    print("Cutting audio...")

    start = 0.0
    for i, end in enumerate(cut_points):
        s = int(start * 1000)
        e = int(end * 1000)
        if e <= s:
            e = s + 150

        out = os.path.join(output_path, f"{i+1}.mp3")
        audio[s:e].export(out, format="mp3")
        print("Saved:", out)
        start = end

    print("Done.")
