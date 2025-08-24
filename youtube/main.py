import image_manager
import voice_manager
import video_manager
import file_manager

#user inputs
is_test = True

#intermediate operations
file_manager.create_directory_if_not_exists("youtube/output")
file_manager.create_directory_if_not_exists("youtube/output/images")
file_manager.create_directory_if_not_exists("youtube/output/voices")
#file_manager.create_directory_if_not_exists("youtube/output/audios")
file_manager.create_directory_if_not_exists("youtube/output/videos")

def create_story_video():
    text_content = file_manager.get_text_content_for_youtube(is_test, False)
    text_parts = text_content.split("***")
    image_manager.create_images(text_parts)
    voice_manager.create_voices(text_parts, True)
    video_manager.create_video_parts(False, "youtube/output/videos")
    video_manager.merge_video_parts("youtube/input/outro.mp4", "youtube/output/videos", "youtube/output/output.mp4")

def create_shorts():
    text_content = file_manager.get_text_content_for_youtube(is_test, True)
    text_parts = text_content.splitlines()
    voice_manager.create_voices(text_parts, True)
    video_manager.create_video_parts(True, "youtube/output/videos")
    video_manager.merge_video_parts("youtube/input/shorts_outro.mp4", "youtube/output/videos", "youtube/output/output.mp4")

def create_questions_and_answers_video():
    text_content = file_manager.get_text_content_for_youtube(is_test, True)
    text_parts = text_content.splitlines()
    voice_manager.create_voices(text_parts, True)
    #voice_manager.clean_voice_files()
    video_manager.create_video_parts(True, "youtube/output/videos")
    video_manager.merge_video_parts("youtube/input/questions_and_answers_outro.mp4", "youtube/output/videos", "youtube/output/output.mp4")
    video_manager.change_video_speed("youtube/output/output.mp4", "youtube/output/video.mp4", 0.9)

#main methods
#data_manager.create_bulk_data()
#create_story_video()
#create_shorts()
create_questions_and_answers_video()
