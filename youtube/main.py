import image_generator
import voice_generator
import video_generator
import file_manager
import data_generator

#user inputs
is_test = False
is_short_video = False
is_using_default_outro = False
#if short video, edit voice_generator.generate_voice_with_text_using_chatgpt_api

#intermediate operations
file_manager.create_directory_if_not_exists("youtube/output")
file_manager.create_directory_if_not_exists("youtube/output/images")
file_manager.create_directory_if_not_exists("youtube/output/voices")
#file_manager.create_directory_if_not_exists("youtube/output/audios")
file_manager.create_directory_if_not_exists("youtube/output/videos")
#text_content = file_manager.get_text_content_for_youtube(is_test, is_short_video)
#text_parts = text_content.splitlines() if is_short_video else text_content.split("***")
#is_using_default_outro = is_using_default_outro and not is_short_video

def create_questions_and_answers_video():
    text_content = file_manager.get_text_content_for_youtube(is_test, True)
    text_parts = text_content.splitlines()
    voice_generator.create_voices(text_parts, True)
    video_generator.create_video_parts()
    video_generator.merge_video_parts(False)
    video_generator.slow_down_video(speed_factor=0.9)

#main methods
#data_generator.create_bulk_data()
#image_generator.create_images(text_parts, is_short_video)
#voice_generator.clean_voice_files()

create_questions_and_answers_video()
