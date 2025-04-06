import image_generator
import voice_generator
import video_generator
import file_manager

#user inputs
is_test = True
is_short_video = False
is_using_default_outro = True

#intermediate operations
file_manager.create_directory_if_not_exists("youtube/output")
file_manager.create_directory_if_not_exists("youtube/output/images")
file_manager.create_directory_if_not_exists("youtube/output/voices")
file_manager.create_directory_if_not_exists("youtube/output/videos")
text_content = file_manager.get_text_content_for_youtube(is_test, is_short_video)
text_parts = text_content.split("***")

#main methods
image_generator.create_images(text_parts)
voice_generator.create_voices(text_parts)
video_generator.create_video_parts()
video_generator.merge_video_parts()
