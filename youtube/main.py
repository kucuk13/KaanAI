import image_generator
import voice_generator
import video_generator
import file_manager
import data_generator

#user inputs
is_test = True

#intermediate operations
file_manager.create_directory_if_not_exists("youtube/output")
file_manager.create_directory_if_not_exists("youtube/output/images")
file_manager.create_directory_if_not_exists("youtube/output/voices")
#file_manager.create_directory_if_not_exists("youtube/output/audios")
file_manager.create_directory_if_not_exists("youtube/output/videos")

def create_questions_and_answers_video():
    text_content = file_manager.get_text_content_for_youtube(is_test, True)
    text_parts = text_content.splitlines()
    voice_generator.create_voices(text_parts, True)
    video_generator.create_video_parts(True)
    video_generator.merge_video_parts("youtube/input/questions_and_answers_outro.mp4")
    video_generator.slow_down_video(speed_factor=0.9)

def create_story_video():
    text_content = file_manager.get_text_content_for_youtube(is_test, False)
    text_parts = text_content.split("***")
    image_generator.create_images(text_parts)
    voice_generator.create_voices(text_parts, True)
    video_generator.create_video_parts(False)
    video_generator.merge_video_parts("youtube/input/outro.mp4")

#main methods
#data_generator.create_bulk_data()
#voice_generator.clean_voice_files()
#create_story_video()
create_questions_and_answers_video()
