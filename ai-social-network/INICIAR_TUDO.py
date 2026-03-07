#!/usr/bin/env python3
"""
🚀 SCRIPT MASTER - INICIA TUDO AUTOMATICAMENTE
Servidor + Comunidade de IAs + Facebook IAs + Auto-Aperfeicoamento
100% Autossuficiente - Roda para sempre!
Sistema de auto-completar e auto-melhorar infinito!
"""

import subprocess
import time
import os
import signal
import sys
import requests

# Diretorio do projeto
DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

# Processos
processos = {}


def log(msg):
    print(f"[MASTER] {msg}")


def verificar_ollama():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        modelos = [m["name"] for m in r.json().get("models", [])]
        log(f"Ollama OK - {len(modelos)} modelos disponiveis")
        return True
    except:
        log("ERRO: Ollama nao esta rodando!")
        log("Execute: ollama serve")
        return False


def verificar_servidor():
    try:
        r = requests.get("http://localhost:8000/health", timeout=5)
        if r.status_code == 200:
            log("Servidor API OK")
            return True
    except:
        pass
    return False


def iniciar_servidor():
    if verificar_servidor():
        log("Servidor ja esta rodando")
        return True

    log("Iniciando servidor...")
    proc = subprocess.Popen(
        ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processos["servidor"] = proc
    time.sleep(5)

    if verificar_servidor():
        log("Servidor iniciado com sucesso!")
        return True
    else:
        log("Falha ao iniciar servidor")
        return False


def iniciar_comunidade():
    log("Iniciando Comunidade de IAs...")
    proc = subprocess.Popen(
        ["python3", "-u", "comunidade_ias.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processos["comunidade"] = proc
    return proc


def iniciar_facebook():
    log("Iniciando Facebook IAs...")
    proc = subprocess.Popen(
        ["python3", "-c", """
import asyncio
from facebook_ias import FacebookIAs

async def rodar():
    fb = FacebookIAs()
    await fb.rodar_para_sempre()

asyncio.run(rodar())
"""],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processos["facebook"] = proc
    return proc


def iniciar_auto_melhorar():
    log("Iniciando Auto-Aperfeicoamento Infinito...")
    proc = subprocess.Popen(
        ["python3", "auto_melhorar.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processos["auto_melhorar"] = proc
    return proc


def parar_tudo(sig=None, frame=None):
    log("\nParando todos os processos...")
    for nome, proc in processos.items():
        if proc and proc.poll() is None:
            proc.terminate()
            log(f"  {nome} parado")
    log("Tudo parado!")
    sys.exit(0)


def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║  🚀 REDE SOCIAL DE IAs - SCRIPT MASTER v2.0                   ║
║  100% Autossuficiente - Roda para sempre!                      ║
║  Auto-completar + Auto-melhorar INFINITO!                      ║
╠════════════════════════════════════════════════════════════════╣
║  Componentes:                                                  ║
║    - Servidor API (FastAPI)                                    ║
║    - Comunidade de IAs (5 perspectivas diferentes)             ║
║    - Facebook IAs (simulacao de usuarios)                      ║
║    - Auto-Aperfeicoamento (melhora sozinho!)                   ║
╠════════════════════════════════════════════════════════════════╣
║  Interfaces:                                                   ║
║    /facebook  - Facebook Dark Mode                             ║
║    /x         - X/Twitter                                      ║
║    /instagram - Instagram (Fotos)                              ║
║    /tiktok    - TikTok (Videos)                                ║
║    /youtube   - YouTube (Videos longos)                        ║
╠════════════════════════════════════════════════════════════════╣
║  Acesse: http://localhost:8000                                 ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Handler para Ctrl+C
    signal.signal(signal.SIGINT, parar_tudo)
    signal.signal(signal.SIGTERM, parar_tudo)

    # Verificar Ollama
    if not verificar_ollama():
        return

    # Iniciar servidor
    if not iniciar_servidor():
        return

    # Iniciar IAs
    time.sleep(2)
    comunidade = iniciar_comunidade()
    time.sleep(3)
    facebook = iniciar_facebook()
    time.sleep(2)
    iniciar_auto_melhorar()

    log("")
    log("="*60)
    log("  TUDO RODANDO! Sistema 100% autossuficiente.")
    log("  Auto-aperfeicoamento ATIVADO - melhora sozinho!")
    log("  Pressione Ctrl+C para parar.")
    log("="*60)
    log("")

    # Mostrar output da comunidade em tempo real
    try:
        while True:
            # Ler output da comunidade
            if comunidade.poll() is None:
                line = comunidade.stdout.readline()
                if line:
                    print(line, end="")
            else:
                log("Comunidade parou! Reiniciando...")
                comunidade = iniciar_comunidade()

            # Verificar se facebook ainda roda
            if facebook.poll() is not None:
                log("Facebook parou! Reiniciando...")
                facebook = iniciar_facebook()

            time.sleep(0.1)

    except KeyboardInterrupt:
        parar_tudo()


if __name__ == "__main__":
    main()
