import os
import subprocess
import re
from moviepy import AudioArrayClip, AudioFileClip, ImageClip, concatenate_audioclips
import numpy as np

silence_duration = 0.2
outro_video = "youtube/input/outro.mp4"
input_folder_for_voices = "youtube/output/voices"
input_folder_for_images = "youtube/output/images"
output_folder = "youtube/output/videos"
concat_list_path = "files_to_concat.txt"

def create_video_parts():
    audio_files = sorted(
        [f for f in os.listdir(input_folder_for_voices) if f.endswith(".mp3")],
        key=numerical_sort
    )
    image_files = sorted(
        [f for f in os.listdir(input_folder_for_images) if f.endswith(".png")],
        key=numerical_sort
    )

    for audio_file in audio_files:
        base_name = os.path.splitext(audio_file)[0]
        matching_images = [img for img in image_files if base_name in img]

        if matching_images:
            image_file = matching_images[0]
            audio_path = os.path.join(input_folder_for_voices, audio_file)
            image_path = os.path.join(input_folder_for_images, image_file)
            audio_clip = AudioFileClip(audio_path)
            silence = AudioArrayClip(np.zeros((int(44100 * silence_duration), 2)), fps=44100)
            full_audio = concatenate_audioclips([audio_clip, silence])
            image_clip = ImageClip(image_path, duration=audio_clip.duration + silence_duration)
            video = image_clip.with_audio(full_audio)
            output_video_path = os.path.join(output_folder, f"{base_name}.mp4")
            video.write_videofile(output_video_path, fps=24, codec="libx264")

def numerical_sort(value):
    numbers = re.findall(r'\d+', value)
    return int(numbers[0]) if numbers else 0

def merge_video_parts(is_using_default_outro):
    video_files = sorted(
        [f for f in os.listdir(output_folder) if f.endswith(".mp4")],
        key=numerical_sort
    )
    
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for vf in video_files:
            full_path = os.path.join(output_folder, vf)
            f.write(f"file '{full_path}'\n")
        if is_using_default_outro and os.path.exists(outro_video):
            f.write(f"file '{outro_video}'\n")
    
    output_path = os.path.join("youtube", "output", "output.mp4")
    
    subprocess.run([
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        output_path
    ])
