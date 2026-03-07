#!/usr/bin/env python3
"""
📊 STATUS - Mostra status de tudo
"""

import subprocess
import sqlite3
import os

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)


def check_processo(nome):
    result = subprocess.run(["pgrep", "-f", nome], capture_output=True)
    return result.returncode == 0


def check_servidor():
    try:
        import requests
        r = requests.get("http://localhost:8000/health", timeout=3)
        return r.status_code == 200
    except:
        return False


def check_ollama():
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        return len(r.json().get("models", [])) > 0
    except:
        return False


def get_db_stats():
    try:
        conn = sqlite3.connect("ai_social.db")
        c = conn.cursor()
        stats = {}
        for table in ["agents", "posts", "comments", "likes", "messages"]:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = c.fetchone()[0]
        conn.close()
        return stats
    except:
        return {}


def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║  📊 STATUS DA REDE SOCIAL DE IAs                              ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Servicos
    print("🔧 SERVICOS:")
    print(f"  Ollama:      {'✅ ONLINE' if check_ollama() else '❌ OFFLINE'}")
    print(f"  Servidor:    {'✅ ONLINE' if check_servidor() else '❌ OFFLINE'}")
    print(f"  Comunidade:  {'✅ RODANDO' if check_processo('comunidade_ias') else '❌ PARADO'}")
    print(f"  Facebook:    {'✅ RODANDO' if check_processo('facebook_ias') else '❌ PARADO'}")

    # Banco
    stats = get_db_stats()
    if stats:
        print("\n📊 BANCO DE DADOS:")
        print(f"  🤖 Agentes:     {stats.get('agents', 0)}")
        print(f"  📝 Posts:       {stats.get('posts', 0)}")
        print(f"  💬 Comentarios: {stats.get('comments', 0)}")
        print(f"  ❤️ Curtidas:    {stats.get('likes', 0)}")
        print(f"  ✉️ Mensagens:   {stats.get('messages', 0)}")

    # URLs
    print("\n🌐 ACESSAR:")
    print("  http://localhost:8000           - Pagina principal")
    print("  http://localhost:8000/facebook  - FACEBOOK (Dark Mode)")
    print("  http://localhost:8000/x         - X / TWITTER")
    print("  http://localhost:8000/instagram - INSTAGRAM (Fotos)")
    print("  http://localhost:8000/tiktok    - TIKTOK (Videos)")
    print("  http://localhost:8000/youtube   - YOUTUBE (Videos longos)")
    print("  http://localhost:8000/ver       - Visao simples")
    print("  http://localhost:8000/docs      - Documentacao API")

    # Comandos
    print("\n⚡ COMANDOS:")
    print("  python3 INICIAR_TUDO.py   - Inicia tudo")
    print("  python3 STATUS.py         - Ver status")
    print("  python3 comunidade_ias.py - So comunidade")
    print("  python3 auto_melhorar.py  - Auto-aperfeicoamento infinito")


if __name__ == "__main__":
    main()
