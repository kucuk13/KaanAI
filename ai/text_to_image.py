from diffusers import StableDiffusionPipeline
import torch

#recommended to use GPU for faster processing
def generate_image_from_gpu(prompt):
    cache_dir = "D:/.cache"
    model_id = "sd-legacy/stable-diffusion-v1-5"
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16, cache_dir=cache_dir)
    pipe = pipe.to("cuda")
    image = pipe(prompt).images[0]
    file_name = f"ai/{prompt}.png"
    image.save(file_name)

#if you don't have a Nvidia GPU, use CPU (slower)
def generate_image_from_cpu(prompt):
    cache_dir = "D:/.cache"
    model_id = "sd-legacy/stable-diffusion-v1-5"
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32, cache_dir=cache_dir)
    pipe = pipe.to("cpu")
    image = pipe(prompt).images[0]
    file_name = f"ai/{prompt}.png"
    image.save(file_name)

generate_image_from_gpu("a photo of an astronaut riding a horse on mars")
