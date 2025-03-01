from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt

# Görüntü boyutlarını belirleme
width, height = 1280, 720

# Arka planı oluşturma (eski kağıt rengi)
background_color = (235, 220, 185)  # Açık kahverengi
image = Image.new("RGB", (width, height), background_color)
draw = ImageDraw.Draw(image)

# Metin içeriği
title = "Hi everyone! Welcome to today's video!"
subtitle = "We are going to learn about something."

# Yazı tipi ve boyutları
def get_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

font_title = get_font(50)
font_subtitle = get_font(40)

# Metni konumlandırma
x, y = 50, 200
draw.text((x, y), title, fill="black", font=font_title)
draw.text((x, y + 100), subtitle, fill="black", font=font_subtitle)

# Görüntüyü gösterme
plt.figure(figsize=(12, 7))
plt.imshow(image)
plt.axis("off")
plt.show()
