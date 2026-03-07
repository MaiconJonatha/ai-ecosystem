#!/usr/bin/env python3
"""
🚀 AI ChatGPT - Script de Inicialização
Auto-gerenciado por IAs locais (Ollama)

Como usar:
    python INICIAR.py

Isso vai:
1. Verificar dependências
2. Inicializar banco de dados
3. Iniciar servidor FastAPI
4. Iniciar sistema de auto-gerenciamento
"""

import subprocess
import sys
import os
import time
import threading
import signal

# Cores para terminal
class Cores:
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    AZUL = '\033[94m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'


def log(emoji: str, msg: str, cor: str = Cores.RESET):
    print(f"{cor}{emoji} {msg}{Cores.RESET}")


def verificar_python():
    """Verifica versão do Python"""
    if sys.version_info < (3, 9):
        log("❌", f"Python 3.9+ necessário (atual: {sys.version})", Cores.VERMELHO)
        sys.exit(1)
    log("✅", f"Python {sys.version_info.major}.{sys.version_info.minor} OK", Cores.VERDE)


def verificar_ollama():
    """Verifica se Ollama está rodando"""
    import httpx

    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        if r.status_code == 200:
            modelos = r.json().get("models", [])
            log("✅", f"Ollama OK - {len(modelos)} modelos disponíveis", Cores.VERDE)
            for m in modelos[:5]:
                log("  🤖", f"  {m['name']}", Cores.AZUL)
            return True
    except:
        pass

    log("⚠️", "Ollama não está rodando", Cores.AMARELO)
    log("💡", "Inicie com: ollama serve", Cores.AMARELO)
    log("💡", "Baixe modelos: ollama pull llama3.2:3b", Cores.AMARELO)
    return False


def verificar_dependencias():
    """Verifica e instala dependências"""
    log("📦", "Verificando dependências...", Cores.AZUL)

    dependencias = [
        "fastapi",
        "uvicorn",
        "httpx",
        "jinja2",
        "python-multipart",
        "pydantic-settings",
        "aiosqlite",
        "sqlalchemy"
    ]

    for dep in dependencias:
        try:
            __import__(dep.replace("-", "_"))
            log("  ✓", f"  {dep}", Cores.VERDE)
        except ImportError:
            log("  📥", f"  Instalando {dep}...", Cores.AMARELO)
            subprocess.run([sys.executable, "-m", "pip", "install", dep, "-q"])

    log("✅", "Dependências OK", Cores.VERDE)


def inicializar_banco():
    """Inicializa banco de dados"""
    log("🗃️", "Inicializando banco de dados...", Cores.AZUL)

    import sqlite3
    conn = sqlite3.connect("ai_chat.db")
    c = conn.cursor()

    # Tabela de conversas
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de mensagens
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            model TEXT,
            tokens INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    # Tabela de gerenciadores de IA
    c.execute("""
        CREATE TABLE IF NOT EXISTS ai_managers (
            id TEXT PRIMARY KEY,
            name TEXT,
            model TEXT,
            role TEXT,
            tasks_completed INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de logs do sistema
    c.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    log("✅", "Banco de dados inicializado", Cores.VERDE)


def iniciar_servidor(porta: int = 8003):
    """Inicia servidor FastAPI"""
    log("🌐", f"Iniciando servidor na porta {porta}...", Cores.AZUL)

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", str(porta),
        "--reload"
    ])


def iniciar_auto_gerenciamento():
    """Inicia sistema de auto-gerenciamento em thread separada"""
    log("🤖", "Iniciando sistema de auto-gerenciamento...", Cores.MAGENTA)

    def run_auto():
        time.sleep(5)  # Esperar servidor iniciar
        subprocess.run([sys.executable, "auto_gerenciar.py"])

    thread = threading.Thread(target=run_auto, daemon=True)
    thread.start()


def main():
    print(f"""
{Cores.MAGENTA}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🤖  AI ChatGPT - Auto-Gerenciado por IAs Locais  🤖     ║
║                                                              ║
║         Llama • Gemma • Phi • Qwen • TinyLlama              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Cores.RESET}
    """)

    # Verificações
    verificar_python()
    verificar_dependencias()
    inicializar_banco()

    ollama_ok = verificar_ollama()
    if not ollama_ok:
        log("⚠️", "Continuando sem Ollama (funcionalidade limitada)", Cores.AMARELO)

    # Iniciar servidor
    porta = 8003
    iniciar_servidor(porta)

    # Iniciar auto-gerenciamento
    iniciar_auto_gerenciamento()

    print(f"""
{Cores.VERDE}
╔══════════════════════════════════════════════════════════════╗
║                    ✅ SISTEMA INICIADO!                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   🌐 Chat:       http://localhost:{porta}                      ║
║   📊 Dashboard:  http://localhost:{porta}/dashboard             ║
║   📚 API Docs:   http://localhost:{porta}/docs                  ║
║                                                              ║
║   🤖 Auto-gerenciamento: ATIVO                               ║
║   ♾️  Loop infinito: RODANDO                                  ║
║                                                              ║
║   Pressione Ctrl+C para encerrar                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Cores.RESET}
    """)

    # Manter processo vivo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("👋", "Encerrando sistema...", Cores.AMARELO)
        sys.exit(0)


if __name__ == "__main__":
    main()
