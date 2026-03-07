"""
LLM Client - Ollama local + Groq cloud fallback
Usado por todos os routers para geracao de texto
"""
import httpx
import os

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Mapeamento Ollama -> Groq models
GROQ_MODEL_MAP = {
    "llama3.2:3b": "llama-3.3-70b-versatile",
    "gemma2:2b": "gemma2-9b-it",
    "phi3:mini": "llama-3.1-8b-instant",
    "qwen2:1.5b": "llama-3.1-8b-instant",
    "tinyllama": "llama-3.1-8b-instant",
    "mistral:7b-instruct": "mixtral-8x7b-32768",
}

_ollama_available = None


async def check_ollama():
    """Verifica se Ollama esta disponivel"""
    global _ollama_available
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            _ollama_available = r.status_code == 200
    except:
        _ollama_available = False
    return _ollama_available


async def gerar_texto(
    modelo: str,
    prompt: str,
    system: str = "",
    max_tokens: int = 150,
    temperature: float = 0.85,
    timeout: float = 60.0,
) -> str:
    """
    Gera texto usando Ollama (local) ou Groq (cloud fallback).
    Retorna string vazia se ambos falharem.
    """
    global _ollama_available

    # Tenta Ollama primeiro (se disponivel)
    if _ollama_available is None:
        await check_ollama()

    if _ollama_available:
        try:
            body = {
                "model": modelo,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            if system:
                body["system"] = system

            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(f"{OLLAMA_URL}/api/generate", json=body)
                if r.status_code == 200:
                    return r.json().get("response", "").strip()
        except:
            _ollama_available = False

    # Fallback: Groq API
    if GROQ_API_KEY:
        try:
            groq_model = GROQ_MODEL_MAP.get(modelo, "llama-3.1-8b-instant")
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(GROQ_URL, headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }, json={
                    "model": groq_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                })
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"].strip()
                else:
                    print(f"[LLM] Groq error {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"[LLM] Groq exception: {e}")

    return ""


async def recheck_ollama():
    """Re-verifica Ollama periodicamente"""
    global _ollama_available
    _ollama_available = None
    return await check_ollama()
