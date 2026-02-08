from diffusers import StableDiffusionPipeline
from enum import Enum
import torch
import os
import re

class StableDiffusionModels(str, Enum):
    LEGACY_SD_V1_5 = "sd-legacy/stable-diffusion-v1-5"
    SD_V1_5 = "runwayml/stable-diffusion-v1-5"
    SD_V2_1 = "stabilityai/stable-diffusion-2-1"
    SDXL_BASE = "stabilityai/stable-diffusion-xl-base-1.0"
    SDXL_REFINER = "stabilityai/stable-diffusion-xl-refiner-1.0"
    SDXL_TURBO = "stabilityai/sdxl-turbo"
    SD3_MEDIUM = "stabilityai/stable-diffusion-3-medium-diffusers"
    SD3_5_LARGE = "stabilityai/stable-diffusion-3.5-large"

"""
recommended to use GPU for faster processing
if you don't have a Nvidia GPU, use CPU (slower)
"""
def generate_image(prompt: str, 
                   use_gpu: bool = True, 
                   model: StableDiffusionModels = StableDiffusionModels.SDXL_BASE, 
                   cache_dir: str = "D:/.cache"):
    
    dtype = torch.float16 if use_gpu and torch.cuda.is_available() else torch.float32
    device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
    print(f"Used device: {device}")

    pipe = StableDiffusionPipeline.from_pretrained(model.value, torch_dtype=dtype, cache_dir=cache_dir)
    pipe = pipe.to(device)

    image = pipe(prompt).images[0]

    safe_prompt = re.sub(r'[^a-zA-Z0-9_\- ]', '_', prompt)
    os.makedirs("ai", exist_ok=True)
    file_name = os.path.join("ai", f"{safe_prompt}.png")
    
    image.save(file_name)
    print(f"Image saved as: {file_name}")

#Example prompt: a photo of an astronaut riding a horse on mars
prompt = input("Enter your prompt: ")
generate_image(prompt, use_gpu=True)
