# Portas dos serviços – como rodar cada projeto

Cada serviço roda em uma porta diferente. Entre na pasta do projeto, instale as dependências e suba o servidor.

| Porta | Projeto            | Comando (dentro da pasta do projeto) |
|-------|--------------------|--------------------------------------|
| 8000  | ai-social-network  | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| 8002  | ai-search-engine   | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload` |
| 8003  | ai-chatgpt         | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload` |
| 8004  | ai-whatsapp        | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload` |
| 8006  | ai-spotify         | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload` |
| 8009  | ai-logs            | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8009 --reload` |
| 8010  | ai-crypto-exchange | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload` |
| 8011  | ai-gta             | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload` |
| 8012  | ai-chess           | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8012 --reload` |
| 8013  | ai-iot             | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8013 --reload` |
| 8014  | ai-video-generator | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8014 --reload` |
| 8015  | ai-shopee-video    | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8015 --reload` |
| 8016  | ai-social-video    | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8016 --reload` |
| 8017  | ai-games           | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8017 --reload` |
| 8018  | ai-messenger       | `pip install -r requirements.txt` → `uvicorn app.main:app --host 0.0.0.0 --port 8018 --reload` |

## Exemplo rápido

```bash
# Exemplo: subir o AI Spotify na porta 8006
cd ai-spotify
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
# Acesse: http://localhost:8006/
```

## Requisitos comuns

- **Ollama** rodando em `http://localhost:11434` para os serviços que usam IA local (Spotify, Chess, Games, Social Network, etc.).
- **Python 3.10+** recomendado.
