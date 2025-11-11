from stable_whisper import load_model
from pydub import AudioSegment
from constants import whisper_model
import re, os

def normalize(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())

def split_voices(sentences, input_voice_file, output_path):
    os.makedirs(output_path, exist_ok=True)
    output_prefix = "part_"

    model = load_model(whisper_model.small.value)
    result = model.transcribe(input_voice_file, regroup=False)
    timings = []

    print("#2")

    for sent in sentences:
        sent_norm = [normalize(w) for w in sent.split()]
        start_time = None
        end_time = None

        for seg in result.segments:
            for w in seg.words:
                word_norm = normalize(w.word)
                if word_norm == sent_norm[0] and start_time is None:
                    start_time = w.start
                if word_norm == sent_norm[-1]:
                    end_time = w.end

        timings.append((sent, start_time, end_time))

    print("#3")

    audio = AudioSegment.from_mp3(input_voice_file)
    for i, (text, start, end) in enumerate(timings):
        if start is None or end is None:
            print(f"Skipped: {text}")
            continue
        piece = audio[int(start*1000):int(end*1000)]
        piece.export(f"{output_path + output_prefix}{i+1}.mp3", format="mp3")

sentences = [
    "Why don't skeletons",
    "fight each other?",
    "They don't have",
    "the guts"
]
split_voices(sentences, "youtube/input/voices/merged_voice.mp3", "youtube/output/voices/")
