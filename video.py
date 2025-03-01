from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import textwrap

def get_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        return ImageFont.load_default()

def show_image(image):
    plt.figure(figsize=(12, 7))
    plt.imshow(image)
    plt.axis("off")
    plt.show()

def save_image(image, output_path="output.png"):
    image.save(output_path)

def generate_image_with_text(title):
    width, height = 1920, 1080
    background_color = (235, 220, 185)
    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)

    font_content = get_font(64)
    
    wrapped_text = textwrap.fill(title, width=40)  # Adjust width as needed
    
    x, y = 50, 200
    draw.text((x, y), wrapped_text, fill="black", font=font_content)
    
    return image

img = generate_image_with_text("Hi everyone! Welcome to today's video! We are going to learn about something.")
#show_image(img)
save_image(img)
