import os
import zipfile

def get_text_from_file(file_name, max_size_mb=10):
    if not file_name.lower().endswith(".txt"):
        raise ValueError(f"File must be a txt file: {file_name}")

    if not os.path.exists(file_name):
        raise ValueError(f"File not found: {file_name}")

    file_size_mb = os.path.getsize(file_name) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValueError(f"File exceeds maximum allowed size ({max_size_mb} MB): {file_size_mb:.2f} MB")
    
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            content = file.read()
        if not content.strip():
            raise ValueError(f"File is empty: {file_name}")
        return content
    except FileNotFoundError:
        raise ValueError(f"No file found with the given name: {file_name}")
    except UnicodeDecodeError:
        raise ValueError(f"File is not a valid UTF-8 text file: {file_name}")
    except OSError as e:
        raise ValueError(f"File could not be opened: {file_name}. Reason: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred while reading the file: {file_name}. Reason: {e}")

def get_lines_from_text_file(file_name):
    content = get_text_from_file(file_name)
    return [line.strip() for line in content.splitlines() if line.strip()]

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

def is_audio_file(file_name):
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"Audio file not found: {file_name}")

    if not file_name.lower().endswith((".mp3", ".wav", ".m4a")):
        raise ValueError(f"Audio file format not supported: {file_name}")
