#!/usr/bin/env python3
"""
🔍 AI SEARCH ENGINE - Mecanismo de Busca gerenciado por IAs
Inicia o servidor e os agentes de IA + Auto-gerenciamento
100% AUTONOMO - SE CONSERTA SOZINHO!
"""
import subprocess
import time
import os
import signal
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

processos = {}


def log(msg):
    print(f"[AI-SEARCH] {msg}")


def iniciar_servidor():
    log("Iniciando servidor...")
    proc = subprocess.Popen(
        ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processos["servidor"] = proc
    time.sleep(3)
    log("Servidor iniciado na porta 8001!")
    return True


def iniciar_auto_gerenciamento():
    log("Iniciando Auto-Gerenciamento por IAs...")
    proc = subprocess.Popen(
        ["python3", "auto_gerenciar.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processos["auto_gerenciar"] = proc
    return proc


def parar_tudo(sig=None, frame=None):
    log("\nParando processos...")
    for nome, proc in processos.items():
        if proc and proc.poll() is None:
            proc.terminate()
            log(f"  {nome} parado")
    log("Tudo parado!")
    sys.exit(0)


def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║  🔍 AI SEARCH ENGINE v2.0                                      ║
║  Mecanismo de Busca 100% gerenciado por IAs                   ║
║  AUTO-GERENCIAVEL + AUTO-CORRIGIVEL!                          ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  Agentes de IA:                                                ║
║    🕷️ Crawler AI   - Rastrea paginas                          ║
║    📑 Indexer AI   - Indexa conteudo                          ║
║    📊 Ranker AI    - Rankeia resultados                       ║
║    🔬 Analyzer AI  - Analisa qualidade                        ║
║    📝 Summarizer AI - Resume conteudo                         ║
║    ⚡ Optimizer AI  - Otimiza buscas                          ║
║                                                                ║
║  Auto-Gerenciamento:                                           ║
║    ✓ Sistema se corrige sozinho                               ║
║    ✓ IAs trabalham autonomamente                              ║
║    ✓ Roda PARA SEMPRE!                                        ║
║                                                                ║
╠════════════════════════════════════════════════════════════════╣
║  Acesse: http://localhost:8001                                 ║
║  Dashboard: http://localhost:8001/dashboard                    ║
╚════════════════════════════════════════════════════════════════╝
    """)

    signal.signal(signal.SIGINT, parar_tudo)
    signal.signal(signal.SIGTERM, parar_tudo)

    iniciar_servidor()
    time.sleep(2)
    auto_proc = iniciar_auto_gerenciamento()

    log("")
    log("="*60)
    log("  AI Search Engine rodando!")
    log("  Auto-gerenciamento ATIVADO - se conserta sozinho!")
    log("  Pressione Ctrl+C para parar.")
    log("="*60)
    log("")

    try:
        while True:
            # Mostrar output do auto-gerenciamento
            if auto_proc.poll() is None:
                line = auto_proc.stdout.readline()
                if line:
                    print(line, end="")
            else:
                log("Auto-gerenciamento parou! Reiniciando...")
                auto_proc = iniciar_auto_gerenciamento()

            time.sleep(0.1)

    except KeyboardInterrupt:
        parar_tudo()


if __name__ == "__main__":
    main()
