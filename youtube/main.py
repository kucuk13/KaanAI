import image_generator
import voice_generator
import video_generator

def get_text_from_file(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "No file found with the given name."
    except Exception as e:
        return f"An error occurred: {e}"

text_content = get_text_from_file("youtube/input/video_script.txt")
text_parts = text_content.split("***")

image_generator.create_images(text_parts)
voice_generator.create_voices(text_parts)
video_generator.create_video_parts()
video_generator.merge_video_parts()
