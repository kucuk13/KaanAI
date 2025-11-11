from stable_whisper import load_model
from pydub import AudioSegment
from constants import whisper_model
import re
import os

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

def split_voices(sentences, input_voice_file, output_path):
    os.makedirs(output_path, exist_ok=True)
    output_prefix = "part_"

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

        out_file = os.path.join(output_path, f"{output_prefix}{i}.mp3")
        audio[int(start * 1000):int(end * 1000)].export(out_file, format="mp3")
        print(f"Saved: {out_file}")

    print("Done.")

# Example usage
if __name__ == "__main__":
    sentences = [
        "Why don't skeletons",
        "fight each other?",
        "They don't have",
        "the guts"
    ]

    split_voices(
        sentences,
        "youtube/input/voices/merged_voice.mp3",
        "youtube/output/voices/"
    )
