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

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_sentence_start(sentence, segments, min_ratio=0.6):
    target_words = [normalize(w) for w in sentence.split() if normalize(w)]
    tlen = len(target_words)
    if tlen == 0:
        return None

    best_start = None
    best_score = 0.0

    for seg in segments:
        words = getattr(seg, "words", None)
        if not words:
            continue

        seg_words = [normalize(w.word) for w in words]
        n = len(seg_words)
        if n == 0:
            continue

        dp = [[0] * (n + 1) for _ in range(tlen + 1)]

        for i in range(1, tlen + 1):
            for j in range(1, n + 1):
                if target_words[i - 1] == seg_words[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        score = dp[tlen][n] / tlen
        if score < min_ratio or score <= best_score:
            continue

        i, j = tlen, n
        matched_indices = []
        while i > 0 and j > 0:
            if target_words[i - 1] == seg_words[j - 1]:
                matched_indices.append(j - 1)
                i -= 1
                j -= 1
            elif dp[i - 1][j] >= dp[i][j - 1]:
                i -= 1
            else:
                j -= 1

        if not matched_indices:
            continue

        first_idx = min(matched_indices)
        best_start = words[first_idx].start
        best_score = score

    return best_start

def split_voices(input_script_file, input_voice_file, output_path):
    sentences = file_manager.get_lines_from_text_file(input_script_file)
    file_manager.is_audio_file(input_voice_file)
    os.makedirs(output_path, exist_ok=True)

    print("Loading model...")
    model = load_model(whisper_model.medium.value)

    print("Transcribing...")
    result = model.transcribe(input_voice_file, regroup=False)

    print("Finding start times...")
    start_times = []

    for i, sentence in enumerate(sentences, start=1):
        if "questionable life decisions" in sentence.lower():
            s = find_sentence_start(sentence, result.segments, min_ratio=0.35)
        else:
            s = find_sentence_start(sentence, result.segments)

        if s is None:
            print(f"NOT FOUND: {sentence}")
            continue

        start_times.append(s)

    if len(start_times) != len(sentences):
        print("Warning: Some timings missing! Skipping missing ones.")

    start_times = sorted(start_times)

    intersection_times = []
    for i in range(len(start_times) - 1):
        mid = (start_times[i] + start_times[i + 1]) / 2
        intersection_times.append(mid)

    cut_points = [0.0] + intersection_times + [start_times[-1] + 10000]

    print("Cutting audio...")
    audio = AudioSegment.from_file(input_voice_file)

    for i in range(len(sentences)):
        start_ms = int(cut_points[i] * 1000)
        end_ms = int(cut_points[i + 1] * 1000)

        out_file = os.path.join(output_path, f"{i+1}.mp3")
        audio[start_ms:end_ms].export(out_file, format="mp3")
        print(f"Saved: {out_file}")

    print("Done.")
