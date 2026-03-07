"""
API FastAPI para Stable Diffusion
Porta: 8013
Gera imagens a partir de texto
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
import torch
from diffusers import StableDiffusionPipeline
import asyncio
import os
import time
import uuid

app = FastAPI(title="AI Image Generator - Stable Diffusion")

pipe = None
IMAGES_DIR = "generated_images"
os.makedirs(IMAGES_DIR, exist_ok=True)

@app.on_event("startup")
async def load_model():
    global pipe
    print("Carregando Stable Diffusion 1.5...")
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16,
        variant="fp16",
        safety_checker=None
    )
    pipe = pipe.to("mps")
    pipe.enable_attention_slicing()
    print("Modelo carregado!")

@app.get("/", response_class=HTMLResponse)
async def home():
    images = sorted(
        [f for f in os.listdir(IMAGES_DIR) if f.endswith(".png")],
        key=lambda x: os.path.getmtime(os.path.join(IMAGES_DIR, x)),
        reverse=True
    )
    gallery = ""
    for img in images[:20]:
        gallery += f'<div style="display:inline-block;margin:10px;text-align:center">'
        gallery += f'<img src="/images/{img}" style="width:256px;height:256px;border-radius:10px">'
        gallery += f'<p style="color:#ccc;font-size:12px">{img}</p></div>'

    return f"""
    <html>
    <head><title>AI Image Generator</title></head>
    <body style="background:#1a1a2e;color:white;font-family:Arial;text-align:center;padding:20px">
        <h1 style="color:#e94560">AI Image Generator</h1>
        <h3 style="color:#0f3460">Stable Diffusion 1.5 - Local</h3>
        <form action="/generate" method="get" style="margin:30px">
            <input type="text" name="prompt" placeholder="Descreva a imagem..."
                style="width:500px;padding:15px;border-radius:10px;border:2px solid #e94560;
                background:#16213e;color:white;font-size:16px">
            <br><br>
            <button type="submit"
                style="padding:15px 40px;background:#e94560;color:white;border:none;
                border-radius:10px;font-size:18px;cursor:pointer">
                Gerar Imagem
            </button>
        </form>
        <div id="gallery">
            <h2 style="color:#0f3460">Galeria</h2>
            {gallery if gallery else '<p style="color:#666">Nenhuma imagem gerada ainda</p>'}
        </div>
    </body>
    </html>
    """

@app.get("/generate")
async def generate(prompt: str, steps: int = 25, width: int = 512, height: int = 512):
    if pipe is None:
        return {"error": "Modelo ainda carregando..."}

    filename = f"{int(time.time())}_{uuid.uuid4().hex[:6]}.png"
    filepath = os.path.join(IMAGES_DIR, filename)

    loop = asyncio.get_event_loop()
    image = await loop.run_in_executor(None, lambda: pipe(
        prompt,
        num_inference_steps=steps,
        guidance_scale=7.5,
        width=width,
        height=height
    ).images[0])

    image.save(filepath)

    return HTMLResponse(f"""
    <html>
    <body style="background:#1a1a2e;color:white;font-family:Arial;text-align:center;padding:20px">
        <h1 style="color:#e94560">Imagem Gerada!</h1>
        <p style="color:#ccc">Prompt: {prompt}</p>
        <img src="/images/{filename}" style="max-width:512px;border-radius:15px;margin:20px">
        <br><br>
        <a href="/" style="color:#e94560;font-size:18px">Voltar e gerar mais</a>
    </body>
    </html>
    """)

@app.get("/images/{filename}")
async def get_image(filename: str):
    filepath = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="image/png")
    return {"error": "Imagem nao encontrada"}

@app.get("/api/generate")
async def api_generate(prompt: str, steps: int = 25):
    """Endpoint API puro - retorna JSON"""
    if pipe is None:
        return {"error": "Modelo ainda carregando..."}

    filename = f"{int(time.time())}_{uuid.uuid4().hex[:6]}.png"
    filepath = os.path.join(IMAGES_DIR, filename)

    loop = asyncio.get_event_loop()
    image = await loop.run_in_executor(None, lambda: pipe(
        prompt,
        num_inference_steps=steps,
        guidance_scale=7.5,
        width=512,
        height=512
    ).images[0])

    image.save(filepath)
    return {
        "status": "ok",
        "prompt": prompt,
        "image_url": f"/images/{filename}",
        "filename": filename
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)
