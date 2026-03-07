"""
API FastAPI - Gerador de Vídeos com Hugging Face
Porta: 8014
Usa HF Inference API + HF Spaces (Wan 2.1)
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
import requests
import asyncio
import os
import time
import uuid

app = FastAPI(title="AI Video Generator - Hugging Face")

HF_TOKEN = os.getenv("HF_TOKEN", "")
VIDEOS_DIR = "generated_videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

generated_videos = []

@app.get("/", response_class=HTMLResponse)
async def home():
    gallery = ""
    for vid in reversed(generated_videos[-20:]):
        gallery += '<div style="display:inline-block;margin:10px;text-align:center;vertical-align:top">'
        gallery += '<video width="256" height="256" controls style="border-radius:10px">'
        gallery += '<source src="/videos/' + vid["filename"] + '" type="video/mp4">'
        gallery += '</video>'
        gallery += '<p style="color:#ccc;font-size:11px;max-width:256px">' + vid["prompt"] + '</p></div>'

    return """
    <html>
    <head><title>AI Video Generator</title></head>
    <body style="background:#0a0a1a;color:white;font-family:Arial;text-align:center;padding:20px">
        <h1 style="color:#00d4ff">AI Video Generator</h1>
        <h3 style="color:#7b68ee">Hugging Face - Gratis</h3>
        <form action="/generate" method="get" style="margin:30px">
            <input type="text" name="prompt" placeholder="Descreva o video em ingles..."
                style="width:500px;padding:15px;border-radius:10px;border:2px solid #00d4ff;
                background:#1a1a3e;color:white;font-size:16px">
            <br><br>
            <select name="method" style="padding:10px;border-radius:8px;background:#1a1a3e;
                color:white;border:1px solid #7b68ee;font-size:14px">
                <option value="api">ModelScope (API - rapido)</option>
                <option value="wan">Wan 2.1 (Spaces - melhor qualidade)</option>
            </select>
            <br><br>
            <button type="submit"
                style="padding:15px 40px;background:linear-gradient(135deg,#00d4ff,#7b68ee);
                color:white;border:none;border-radius:10px;font-size:18px;cursor:pointer">
                Gerar Video
            </button>
        </form>
        <p style="color:#666;font-size:12px">Dica: Descreva em ingles para melhores resultados</p>
        <div id="gallery">
            <h2 style="color:#7b68ee">Videos Gerados</h2>
            """ + (gallery if gallery else '<p style="color:#444">Nenhum video gerado ainda</p>') + """
        </div>
    </body>
    </html>
    """

@app.get("/generate")
async def generate(prompt: str, method: str = "api"):
    if method == "wan":
        return await generate_wan(prompt)
    else:
        return await generate_modelscope(prompt)

async def generate_modelscope(prompt: str):
    """Gera via HF Inference API (ModelScope)"""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    API_URL = "https://router.huggingface.co/hf-inference/models/ali-vilab/text-to-video-ms-1.7b"

    loop = asyncio.get_event_loop()

    def _generate():
        return requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=300)

    try:
        response = await loop.run_in_executor(None, _generate)

        if response.status_code == 200:
            filename = f"ms_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp4"
            filepath = os.path.join(VIDEOS_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            generated_videos.append({"filename": filename, "prompt": prompt, "method": "modelscope"})

            return HTMLResponse(f"""
            <html>
            <body style="background:#0a0a1a;color:white;font-family:Arial;text-align:center;padding:20px">
                <h1 style="color:#00d4ff">Video Gerado!</h1>
                <p style="color:#ccc">Prompt: {prompt}</p>
                <p style="color:#7b68ee">Metodo: ModelScope API</p>
                <video width="512" controls autoplay style="border-radius:15px;margin:20px">
                    <source src="/videos/{filename}" type="video/mp4">
                </video>
                <br><br>
                <a href="/" style="color:#00d4ff;font-size:18px">Voltar e gerar mais</a>
            </body></html>
            """)
        elif response.status_code == 503:
            return HTMLResponse(f"""
            <html>
            <body style="background:#0a0a1a;color:white;font-family:Arial;text-align:center;padding:40px">
                <h1 style="color:#ff6b6b">Modelo Carregando...</h1>
                <p style="color:#ccc">O modelo esta sendo carregado nos servidores do HF.</p>
                <p style="color:#ccc">Tente novamente em 30-60 segundos.</p>
                <br><a href="/" style="color:#00d4ff;font-size:18px">Voltar</a>
            </body></html>
            """)
        else:
            return {"error": response.status_code, "detail": response.text}
    except Exception as e:
        return {"error": str(e)}

async def generate_wan(prompt: str):
    """Gera via Wan 2.1 Space"""
    loop = asyncio.get_event_loop()

    def _generate():
        from gradio_client import Client
        client = Client("Wan-AI/Wan2.1")
        result = client.predict(prompt=prompt, api_name="/generate")
        return result

    try:
        result = await loop.run_in_executor(None, _generate)
        filename = f"wan_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp4"
        filepath = os.path.join(VIDEOS_DIR, filename)

        if isinstance(result, str) and os.path.exists(result):
            import shutil
            shutil.copy2(result, filepath)
        else:
            return {"error": "Resultado inesperado", "result": str(result)}

        generated_videos.append({"filename": filename, "prompt": prompt, "method": "wan2.1"})

        return HTMLResponse(f"""
        <html>
        <body style="background:#0a0a1a;color:white;font-family:Arial;text-align:center;padding:20px">
            <h1 style="color:#00d4ff">Video Gerado!</h1>
            <p style="color:#ccc">Prompt: {prompt}</p>
            <p style="color:#7b68ee">Metodo: Wan 2.1 (Spaces)</p>
            <video width="512" controls autoplay style="border-radius:15px;margin:20px">
                <source src="/videos/{filename}" type="video/mp4">
            </video>
            <br><br>
            <a href="/" style="color:#00d4ff;font-size:18px">Voltar e gerar mais</a>
        </body></html>
        """)
    except Exception as e:
        return HTMLResponse(f"""
        <html>
        <body style="background:#0a0a1a;color:white;font-family:Arial;text-align:center;padding:40px">
            <h1 style="color:#ff6b6b">Erro no Wan 2.1</h1>
            <p style="color:#ccc">{str(e)}</p>
            <p style="color:#666">O Space pode estar ocupado. Tente ModelScope.</p>
            <br><a href="/" style="color:#00d4ff;font-size:18px">Voltar</a>
        </body></html>
        """)

@app.get("/videos/{filename}")
async def get_video(filename: str):
    filepath = os.path.join(VIDEOS_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="video/mp4")
    return {"error": "Video nao encontrado"}

@app.get("/api/generate")
async def api_generate(prompt: str, method: str = "api"):
    """Endpoint API puro - retorna JSON"""
    if method == "api":
        headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        response = requests.post(
            "https://router.huggingface.co/hf-inference/models/ali-vilab/text-to-video-ms-1.7b",
            headers=headers,
            json={"inputs": prompt},
            timeout=300
        )
        if response.status_code == 200:
            filename = f"api_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp4"
            filepath = os.path.join(VIDEOS_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            return {"status": "ok", "prompt": prompt, "video_url": f"/videos/{filename}"}
        return {"error": response.status_code, "detail": response.text}
    return {"error": "Use method=api para JSON endpoint"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014)
