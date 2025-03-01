from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import textwrap

def get_font(size):
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except IOError:
        return ImageFont.load_default()

def get_text_from_file(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return file.readlines()
    except FileNotFoundError:
        return ["No file found with the given name."]
    except Exception as e:
        return [f"An error occurred: {e}"]

def show_image(image):
    plt.figure(figsize=(12, 7))
    plt.imshow(image)
    plt.axis("off")
    plt.show()

def save_image(image, output_path="output.png"):
    image.save(output_path)

def generate_image_with_text(text_lines, wrap_width=40):
    width, height = 1920, 1080
    background_color = (235, 220, 185)
    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)

    font_content = get_font(72)
    
    x, y = 50, 200
    line_spacing = 60

    for line in text_lines:
        wrapped_lines = textwrap.wrap(line.strip(), width=wrap_width)
        for wrapped_line in wrapped_lines:
            draw.text((x, y), wrapped_line, fill="black", font=font_content)
            y += line_spacing

    return image

text_lines = get_text_from_file("video_script.txt")
img = generate_image_with_text(text_lines, wrap_width=50)
#show_image(img)
save_image(img)
