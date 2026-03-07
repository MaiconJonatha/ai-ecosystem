#!/usr/bin/env python3
"""
🚀 INICIAR TUDO - Script de Inicialização Universal
════════════════════════════════════════════════════

Este script inicia TODOS os sistemas de IA de uma vez:
- AI Social Network (porta 8000)
- AI Search Engine (porta 8002)
- AI ChatGPT (porta 8003)
- AI WhatsApp (porta 8004)
- Gerenciador Central (coordena todos)

100% AUTO-GERENCIADO POR IAs LOCAIS (OLLAMA)
"""

import subprocess
import sys
import os
import time

# Cores
class C:
    V = '\033[92m'  # Verde
    A = '\033[93m'  # Amarelo
    R = '\033[91m'  # Vermelho
    B = '\033[94m'  # Azul
    M = '\033[95m'  # Magenta
    X = '\033[0m'   # Reset


def main():
    print(f"""
{C.M}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🚀🚀🚀   INICIAR TUDO - ECOSSISTEMA DE IAs AUTO-GERENCIADAS   🚀🚀🚀     ║
║                                                                              ║
║   📱 Social Network  🔍 Search Engine  💬 ChatGPT  📲 WhatsApp              ║
║                                                                              ║
║   Gerenciado por: 🦙 Llama │ ✨ Gemini │ 💎 Gemma │ 🔬 Phi │ 🐉 Qwen      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.X}
    """)

    # Verificar Ollama
    print(f"{C.B}[1/4] Verificando Ollama...{C.X}")
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        if r.status_code == 200:
            modelos = r.json().get("models", [])
            print(f"{C.V}  ✓ Ollama OK - {len(modelos)} modelos{C.X}")
        else:
            raise Exception()
    except:
        print(f"{C.A}  ⚠ Ollama não detectado{C.X}")
        print(f"{C.A}  Execute: ollama serve{C.X}")

    # Instalar dependências
    print(f"\n{C.B}[2/4] Instalando dependências...{C.X}")
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-q",
        "fastapi", "uvicorn", "httpx", "jinja2",
        "python-multipart", "pydantic-settings",
        "aiosqlite", "sqlalchemy"
    ])
    print(f"{C.V}  ✓ Dependências instaladas{C.X}")

    # Diretório base
    base = os.path.dirname(os.path.abspath(__file__))

    # Iniciar sistemas
    print(f"\n{C.B}[3/4] Iniciando sistemas...{C.X}")

    sistemas = [
        ("ai-social-network", 8000, "📱"),
        ("ai-search-engine", 8002, "🔍"),
        ("ai-chatgpt", 8003, "💬"),
        ("ai-whatsapp", 8004, "📲"),
        ("ai-messenger", 8005, "💬"),
        ("ai-spotify", 8006, "🎵"),
        ("ai-chess", 8007, "♟️"),
        ("ai-games", 8008, "🎮"),
        ("ai-logs", 8009, "📊"),
        ("ai-crypto-exchange", 8010, "💰"),
    ]

    processos = []
    for sistema, porta, emoji in sistemas:
        caminho = os.path.join(base, sistema)
        if os.path.exists(caminho):
            print(f"  {emoji} Iniciando {sistema} na porta {porta}...")
            p = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app",
                 "--host", "0.0.0.0", "--port", str(porta)],
                cwd=caminho,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            processos.append(p)
            print(f"{C.V}  ✓ {sistema} iniciado{C.X}")
        else:
            print(f"{C.R}  ✗ {sistema} não encontrado{C.X}")

    time.sleep(3)

    # Iniciar auto-gerenciamento
    print(f"\n{C.B}[4/4] Iniciando auto-gerenciamento...{C.X}")

    for sistema, _, emoji in sistemas:
        caminho = os.path.join(base, sistema)
        auto_file = None

        for f in ["auto_gerenciar.py", "auto_melhorar.py"]:
            if os.path.exists(os.path.join(caminho, f)):
                auto_file = f
                break

        if auto_file:
            print(f"  {emoji} Auto-gerenciamento de {sistema}...")
            subprocess.Popen(
                [sys.executable, auto_file],
                cwd=caminho,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    print(f"""
{C.V}
╔══════════════════════════════════════════════════════════════════════════════╗
║                          ✅ TUDO INICIADO! ✅                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   📱 Social Network:  http://localhost:8000  │  🔍 Search:  http://localhost:8002   ║
║   💬 ChatGPT:         http://localhost:8003  │  📲 WhatsApp: http://localhost:8004  ║
║   💬 Messenger:       http://localhost:8005  │  🎵 Spotify:  http://localhost:8006  ║
║   ♟️ Chess:           http://localhost:8007  │  🎮 Games:    http://localhost:8008  ║
║                                                                              ║
║   📊 LOGS (TEMPO REAL): http://localhost:8009                                ║
║   💰 CRYPTO EXCHANGE:   http://localhost:8010  (Bitcoin, ETH, moedas das IAs)║
║                                                                              ║
║   🤖 Auto-gerenciamento: ATIVO em todos os sistemas                          ║
║   ⛓️  Blockchain: ATIVO para cada IA                                         ║
║   ♾️  Loop infinito: RODANDO                                                  ║
║                                                                              ║
║   Pressione Ctrl+C para encerrar                                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.X}
    """)

    # Manter vivo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{C.A}Encerrando sistemas...{C.X}")
        for p in processos:
            try:
                p.terminate()
            except:
                pass
        print(f"{C.V}Sistemas encerrados{C.X}")


if __name__ == "__main__":
    main()
