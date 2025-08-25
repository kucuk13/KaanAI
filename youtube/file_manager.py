import os
import zipfile

def get_text_from_file(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "No file found with the given name."
    except Exception as e:
        return f"An error occurred: {e}"

def get_text_content_for_youtube(is_test, is_short_video):
    if is_test and is_short_video:
        return get_text_from_file("youtube/input/test_shorts_script.txt")
    elif is_test and not is_short_video:
        return get_text_from_file("youtube/input/test_video_script.txt")
    else:
        return get_text_from_file("youtube/input/video_script.txt")

def create_directory_if_not_exists(directory_name):
    try:
        os.makedirs(directory_name, exist_ok=True)
    except Exception as e:
        return f"An error occurred while creating the directory: {e}"

def extract_zip(input_folder_for_images, input_zip_folder_for_images):
    os.makedirs(input_folder_for_images, exist_ok=True)
    with zipfile.ZipFile(input_zip_folder_for_images, 'r') as archive:
        archive.extractall(path=input_folder_for_images)
