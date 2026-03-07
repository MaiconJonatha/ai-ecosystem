"""
Stable Diffusion - Gerador de Imagens via Python
Funciona no MacBook Air M1 8GB
"""
from diffusers import StableDiffusionPipeline
import torch

print("Carregando modelo Stable Diffusion 1.5...")
print("(primeira vez demora mais porque baixa o modelo ~4GB)")

pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    variant="fp16",
    safety_checker=None
)

# Otimizado para Mac M1
pipe = pipe.to("mps")  # Metal Performance Shaders (GPU Apple)
pipe.enable_attention_slicing()  # economiza memoria

prompt = "a beautiful sunset over the ocean, digital art, 4k"

print(f"Gerando imagem: '{prompt}'")
image = pipe(
    prompt,
    num_inference_steps=25,
    guidance_scale=7.5,
    width=512,
    height=512
).images[0]

output_path = "imagem_gerada.png"
image.save(output_path)
print(f"Imagem salva em: {output_path}")
