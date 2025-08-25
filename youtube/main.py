import image_manager
import voice_manager
import video_manager
import file_manager

#user inputs
is_test = True
images_folder_path = "youtube/input/images"
voices_folder_path = "youtube/input/voices"
videos_folder_path = "youtube/input/videos"
output_file_path = "youtube/output/output.mp4"

#intermediate operations
file_manager.create_directory_if_not_exists("youtube/output")
file_manager.create_directory_if_not_exists(images_folder_path)
file_manager.create_directory_if_not_exists(voices_folder_path)
#file_manager.create_directory_if_not_exists("youtube/output/audios")
file_manager.create_directory_if_not_exists(videos_folder_path)

def create_story_video():
    text_content = file_manager.get_text_content_for_youtube(is_test, False)
    text_parts = text_content.split("***")
    image_manager.create_images(text_parts)
    voice_manager.create_voices(text_parts, True)
    video_manager.create_video_parts(images_folder_path, voices_folder_path, videos_folder_path, 0.5)
    video_manager.merge_video_parts("youtube/input/outro.mp4", videos_folder_path, output_file_path)

def create_shorts():
    text_content = file_manager.get_text_content_for_youtube(is_test, True)
    text_parts = text_content.splitlines()
    voice_manager.create_voices(text_parts, True)
    file_manager.extract_zip(images_folder_path, "youtube/input/images.zip")
    video_manager.create_video_parts(images_folder_path, voices_folder_path, videos_folder_path, 0.5)
    video_manager.merge_video_parts("youtube/input/shorts_outro.mp4", videos_folder_path, output_file_path)

def create_questions_and_answers_video():
    text_content = file_manager.get_text_content_for_youtube(is_test, True)
    text_parts = text_content.splitlines()
    voice_manager.create_voices(text_parts, True)
    #voice_manager.clean_voice_files()
    file_manager.extract_zip(images_folder_path, "youtube/input/images.zip")
    video_manager.create_video_parts(images_folder_path, voices_folder_path, videos_folder_path, 0.5)
    video_manager.merge_video_parts("youtube/input/questions_and_answers_outro.mp4", videos_folder_path, output_file_path)
    video_manager.change_video_speed(output_file_path, "youtube/output/video.mp4", 0.9)

#main methods
#data_manager.create_bulk_data()
#create_story_video()
#create_shorts()
create_questions_and_answers_video()
