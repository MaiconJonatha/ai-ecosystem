"""
Hugging Face - Gerador de Vídeos via API Grátis
Usa a Inference API (sem precisar de GPU local)
"""
import requests
import os
import time

API_TOKEN = os.getenv("HF_TOKEN", "COLOQUE_SEU_TOKEN_AQUI")
headers = {"Authorization": f"Bearer {API_TOKEN}"}

VIDEOS_DIR = "generated_videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

def generate_video_modelscope(prompt: str, filename: str = None):
    """Gera vídeo usando ModelScope Text-to-Video (via HF API grátis)"""
    print(f"Gerando vídeo com ModelScope: '{prompt}'")
    API_URL = "https://router.huggingface.co/hf-inference/models/ali-vilab/text-to-video-ms-1.7b"
    
    response = requests.post(
        API_URL,
        headers=headers,
        json={"inputs": prompt}
    )
    
    if response.status_code == 200:
        if not filename:
            filename = f"video_{int(time.time())}.mp4"
        filepath = os.path.join(VIDEOS_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"Video salvo: {filepath}")
        return filepath
    elif response.status_code == 503:
        print("Modelo carregando... tente novamente em 30-60 segundos")
        print(response.json())
        return None
    else:
        print(f"Erro {response.status_code}: {response.text}")
        return None

def generate_video_via_space(prompt: str):
    """Gera vídeo usando Hugging Face Spaces (Wan 2.1) via API"""
    from gradio_client import Client
    
    print(f"Conectando ao Wan 2.1 Space...")
    client = Client("Wan-AI/Wan2.1")
    
    print(f"Gerando vídeo: '{prompt}'")
    result = client.predict(
        prompt=prompt,
        api_name="/generate"
    )
    print(f"Video gerado: {result}")
    return result

if __name__ == "__main__":
    print("=" * 50)
    print("HUGGING FACE VIDEO GENERATOR")
    print("=" * 50)
    print()
    print("Metodo 1: API Inference (ModelScope)")
    print("Metodo 2: Spaces (Wan 2.1)")
    print()
    
    # Metodo 1 - API direta
    prompt = "a cat walking in a garden, sunny day"
    result = generate_video_modelscope(prompt)
    
    if result:
        print(f"\nSucesso! Video em: {result}")
    else:
        print("\nAPI pode estar carregando. Tentando via Spaces...")
        try:
            result = generate_video_via_space(prompt)
            print(f"Sucesso via Spaces! {result}")
        except Exception as e:
            print(f"Erro no Spaces: {e}")
            print("\nDica: Instale gradio_client com: pip3 install gradio_client")
