#!/usr/bin/env python3
"""🚀 AI Messenger - Inicialização"""

import subprocess, sys, os, time, threading

class C:
    V, A, B, M, X = '\033[92m', '\033[93m', '\033[94m', '\033[95m', '\033[0m'

def main():
    print(f"""
{C.M}
╔════════════════════════════════════════════════════╗
║      💬  AI Messenger - Auto-Gerenciado  💬       ║
║                                                    ║
║   🦙 Llama │ ✨ Gemini │ 💎 Gemma │ 🔬 Phi │ 🐉   ║
╚════════════════════════════════════════════════════╝
{C.X}
    """)

    print(f"{C.B}[1/2] Dependências...{C.X}")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q",
        "fastapi", "uvicorn", "httpx", "jinja2", "python-multipart",
        "pydantic-settings", "aiosqlite", "sqlalchemy"])
    print(f"{C.V}  ✓ OK{C.X}")

    print(f"{C.B}[2/2] Iniciando...{C.X}")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0", "--port", "8005", "--reload"])

    def auto():
        time.sleep(5)
        subprocess.run([sys.executable, "auto_gerenciar.py"])

    threading.Thread(target=auto, daemon=True).start()

    print(f"""
{C.V}
╔════════════════════════════════════════════════════╗
║              ✅ MESSENGER INICIADO!                ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║   💬 Messenger:  http://localhost:8005             ║
║   🤖 Auto-gerenciamento: ATIVO                     ║
║                                                    ║
║   Ctrl+C para encerrar                             ║
╚════════════════════════════════════════════════════╝
{C.X}
    """)

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print(f"{C.A}Encerrando...{C.X}")

if __name__ == "__main__":
    main()
