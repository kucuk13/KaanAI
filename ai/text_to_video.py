import torch
import os
import re
from diffusers import AutoencoderKLWan, WanPipeline
from diffusers.utils import export_to_video
from enum import Enum
from pathlib import Path

class DiffUsersModels(str, Enum):
    SMALL = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
    LARGE = "Wan-AI/Wan2.1-T2V-14B-Diffusers"

def generate_video(prompt: str, 
                   model: DiffUsersModels = DiffUsersModels.SMALL, 
                   cache_dir: str = "D:/.cache"):
    
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_path)
    os.environ["HF_HUB_CACHE"] = str(cache_path / "hub")
    os.environ["TRANSFORMERS_CACHE"] = str(cache_path / "transformers")
    os.environ["DIFFUSERS_CACHE"] = str(cache_path / "diffusers")
    
    vae = AutoencoderKLWan.from_pretrained(model.value, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanPipeline.from_pretrained(model.value, vae=vae, torch_dtype=torch.bfloat16, cache_dir=cache_dir)
    pipe.to("cuda")

    negative_prompt = "Bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards"

    output = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        height=480,
        width=832,
        num_frames=81,
        guidance_scale=5.0
    ).frames[0]

    safe_prompt = re.sub(r'[^a-zA-Z0-9_\- ]', '_', prompt)
    os.makedirs("ai", exist_ok=True)
    file_name = os.path.join("ai", f"{safe_prompt}.png")
    
    export_to_video(output, file_name, fps=15)
    print(f"Video saved as: {file_name}")

#Example prompt: A cat walks on the grass, realistic
prompt = input("Enter your prompt: ")
generate_video(prompt)
