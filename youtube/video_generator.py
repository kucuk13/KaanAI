import os
from moviepy import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips

def create_video_parts():
    input_folder_for_voices = "youtube/output/voices"
    input_folder_for_images = "youtube/output/images"
    output_folder = "youtube/output/videos"
    
    os.makedirs(output_folder, exist_ok=True)

    audio_files = os.listdir(input_folder_for_voices)
    image_files = os.listdir(input_folder_for_images)

    for audio_file in audio_files:
        base_name = os.path.splitext(audio_file)[0]
        matching_images = [img for img in image_files if base_name in img]

        if matching_images:
            image_file = matching_images[0]
            audio_path = os.path.join(input_folder_for_voices, audio_file)
            image_path = os.path.join(input_folder_for_images, image_file)
            audio_clip = AudioFileClip(audio_path)
            image_clip = ImageClip(image_path, duration=audio_clip.duration)
            video = image_clip.with_audio(audio_clip)
            output_video_path = os.path.join(output_folder, f"{base_name}.mp4")
            video.write_videofile(output_video_path, fps=24, codec="libx264")

def merge_video_parts():
    output_folder = "youtube/output/videos"
    video_files = sorted([f for f in os.listdir(output_folder) if f.endswith(".mp4")])
    clips = [VideoFileClip(os.path.join(output_folder, video)) for video in video_files]
    final_clip = concatenate_videoclips(clips, method="compose")
    output_path = os.path.join("youtube/output/output.mp4")
    final_clip.write_videofile(output_path, codec="libx264", fps=24)
    for clip in clips:
        clip.close()
