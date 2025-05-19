import rarfile
import os
import subprocess
import re
from moviepy import AudioArrayClip, AudioFileClip, ImageClip, concatenate_audioclips
import numpy as np

silence_duration = 0.1
outro_video = "youtube/input/outro.mp4"
input_folder_for_voices = "youtube/output/voices"
input_folder_for_images = "youtube/output/images"
input_rar_folder_for_images = "youtube/input/images.rar"
output_folder = "youtube/output/videos"
concat_list_path = "files_to_concat.txt"

def create_video_parts(is_rar):
    audio_files = sorted(
        [f for f in os.listdir(input_folder_for_voices) if f.endswith(".mp3")],
        key=numerical_sort
    )
    
    if is_rar:
        os.makedirs(input_folder_for_images, exist_ok=True)
        with rarfile.RarFile(input_rar_folder_for_images) as archive:
            archive.extractall(path=input_folder_for_images)
        image_files = sorted(
            [f for f in os.listdir(input_folder_for_images) if f.endswith(".png")],
            key=numerical_sort
        )
    else:
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
    
    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-strict", "experimental",
        "-b:a", "192k",
        "-preset", "fast",
        output_path
    ]
    
    subprocess.run(cmd, check=True)

def slow_down_video(speed_factor=0.9):
    input_video = os.path.join("youtube", "output", "output.mp4")
    output_video = os.path.join("youtube", "output", "video.mp4")
    
    if not os.path.exists(input_video):
        raise FileNotFoundError(f"Input video not found: {input_video}")
    
    setpts_value = str(round(1 / speed_factor, 4))
    atempo_value = str(speed_factor)
    
    cmd = [
        "ffmpeg",
        "-i", input_video,
        "-filter_complex", f"[0:v]setpts={setpts_value}*PTS[v];[0:a]atempo={atempo_value}[a]",
        "-map", "[v]",
        "-map", "[a]",
        "-preset", "fast",
        output_video
    ]
    
    subprocess.run(cmd, check=True)
