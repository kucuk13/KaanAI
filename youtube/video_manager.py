import os
import subprocess
from moviepy import AudioArrayClip, AudioFileClip, ImageClip, concatenate_audioclips
import numpy as np
import sort_manager

def create_video_parts(input_folder_for_images, input_folder_for_voices, output_video_path, silence_duration=0.5):
    audio_files = sorted(
        [f for f in os.listdir(input_folder_for_voices) if f.endswith(".mp3")],
        key=sort_manager.numerical_sort
    )
    
    image_files = sorted(
        [f for f in os.listdir(input_folder_for_images) if f.endswith(".png")],
        key=sort_manager.numerical_sort
    )
    
    for audio_file in audio_files:
        base_name = os.path.splitext(audio_file)[0]
        matching_images = [img for img in image_files if base_name in img]

        if matching_images:
            image_file = matching_images[0]
            audio_path = os.path.join(input_folder_for_voices, audio_file)
            image_path = os.path.join(input_folder_for_images, image_file)
            audio_clip = AudioFileClip(audio_path)
            if silence_duration > 0:
                fps = 44100
                samples = int(fps * silence_duration)
                silence_audio = np.zeros((samples, 2), dtype=np.float32)
                silence = AudioArrayClip(silence_audio, fps=fps)

                full_audio = concatenate_audioclips([audio_clip, silence])
                total_duration = audio_clip.duration + silence_duration
            else:
                full_audio = audio_clip
                total_duration = audio_clip.duration
            image_clip = ImageClip(image_path, duration=total_duration)
            video = image_clip.with_audio(full_audio)
            output_path = os.path.join(output_video_path, f"{base_name}.mp4")
            video.write_videofile(output_path, fps=24, codec="libx264")

def merge_video_parts(outro_video_path, input_videos_path, output_video_path):
    concat_list_path = "files_to_concat.txt"
    
    video_files = sorted(
        [f for f in os.listdir(input_videos_path) if f.endswith(".mp4")],
        key=sort_manager.numerical_sort
    )
    
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for vf in video_files:
            full_path = os.path.join(input_videos_path, vf)
            f.write(f"file '{full_path}'\n")
        if os.path.exists(outro_video_path):
            f.write(f"file '{outro_video_path}'\n")
    
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
        output_video_path
    ]
    
    subprocess.run(cmd, check=True)

def _has_audio(input_video_path: str) -> bool:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
        input_video_path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() != ""

def change_video_speed(input_video_path, output_video_path, speed_factor):
    if not os.path.exists(input_video_path):
        raise FileNotFoundError(f"Input video not found: {input_video_path}")
    if speed_factor <= 0:
        raise ValueError("speed_factor must be > 0")

    # Video: setpts = 1/speed
    setpts_value = round(1 / speed_factor, 4)

    # ffmpeg'in atempo aralığı 0.5 - 2.0 (gerekirse zincirlemek gerekir)
    atempo_value = speed_factor

    has_audio = _has_audio(input_video_path)

    if has_audio:
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video_path,
            "-filter_complex", f"[0:v]setpts={setpts_value}*PTS[v];[0:a]atempo={atempo_value}[a]",
            "-map", "[v]",
            "-map", "[a]",
            "-preset", "fast",
            output_video_path
        ]
    else:
        # Audio yoksa: sadece video filtrele, audio map etme
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video_path,
            "-filter:v", f"setpts={setpts_value}*PTS",
            "-an",
            "-preset", "fast",
            output_video_path
        ]

    subprocess.run(cmd, check=True)

