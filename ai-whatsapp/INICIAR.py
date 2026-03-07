#!/usr/bin/env python3
"""
🚀 AI WhatsApp - Inicialização
"""

import subprocess
import sys
import os
import time
import threading

class C:
    V = '\033[92m'
    A = '\033[93m'
    B = '\033[94m'
    M = '\033[95m'
    X = '\033[0m'


def main():
    print(f"""
{C.M}
╔══════════════════════════════════════════════════════════════╗
║          💬  AI WhatsApp - Auto-Gerenciado por IAs  💬       ║
║                                                              ║
║         🦙 Llama │ 💎 Gemma │ 🔬 Phi │ 🐉 Qwen │ 🐣 Tiny    ║
╚══════════════════════════════════════════════════════════════╝
{C.X}
    """)

    # Instalar dependências
    print(f"{C.B}[1/3] Instalando dependências...{C.X}")
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-q",
        "fastapi", "uvicorn", "httpx", "jinja2",
        "python-multipart", "pydantic-settings", "aiosqlite", "sqlalchemy"
    ])
    print(f"{C.V}  ✓ OK{C.X}")

    # Verificar Ollama
    print(f"{C.B}[2/3] Verificando Ollama...{C.X}")
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        if r.status_code == 200:
            modelos = len(r.json().get("models", []))
            print(f"{C.V}  ✓ Ollama OK - {modelos} modelos{C.X}")
    except:
        print(f"{C.A}  ⚠ Ollama não detectado{C.X}")

    # Iniciar servidor
    print(f"{C.B}[3/3] Iniciando servidor...{C.X}")

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Servidor
    subprocess.Popen([
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0", "--port", "8004", "--reload"
    ])

    # Auto-gerenciamento
    def run_auto():
        time.sleep(5)
        subprocess.run([sys.executable, "auto_gerenciar.py"])

    threading.Thread(target=run_auto, daemon=True).start()

    print(f"""
{C.V}
╔══════════════════════════════════════════════════════════════╗
║                    ✅ SISTEMA INICIADO!                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   💬 AI WhatsApp:  http://localhost:8004                     ║
║   📊 Dashboard:    http://localhost:8004/dashboard           ║
║                                                              ║
║   🤖 Auto-gerenciamento: ATIVO                               ║
║   ♾️  Loop infinito: RODANDO                                  ║
║                                                              ║
║   Pressione Ctrl+C para encerrar                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{C.X}
    """)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"{C.A}Encerrando...{C.X}")


if __name__ == "__main__":
    main()
