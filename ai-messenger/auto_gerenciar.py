"""
🤖 AI Messenger - Sistema de Auto-Gerenciamento
100% gerenciado por IAs locais (Ollama)
LOOP INFINITO
"""

import asyncio
import httpx
import sqlite3
from datetime import datetime

OLLAMA_URL = "http://localhost:11434"
DATABASE = "ai_messenger.db"
LOOP_INTERVAL = 30


def log(emoji, msg, level="INFO"):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {emoji} [{level}] {msg}")
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO system_logs (level, message, agent) VALUES (?, ?, ?)", (level, msg, emoji))
        conn.commit()
        conn.close()
    except:
        pass


async def verificar_ollama():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            return r.status_code == 200
    except:
        return False


async def gerenciar():
    log("🦙", "Gerenciando sistema...")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE ai_contacts SET status = 'active'")
    c.execute("DELETE FROM system_logs WHERE created_at < datetime('now', '-24 hours')")
    conn.commit()
    conn.close()
    log("🦙", "Gerenciamento ✓")


async def otimizar():
    log("💎", "Otimizando...")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM messages")
    total = c.fetchone()[0]
    log("💎", f"Total mensagens: {total}")
    c.execute("VACUUM")
    conn.close()
    log("💎", "Otimização ✓")


async def monitorar():
    log("🐣", "Monitorando...")
    ollama_ok = await verificar_ollama()
    log("🐣", f"Ollama: {'✓' if ollama_ok else '✗'}")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ai_contacts")
    contatos = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM conversations")
    convs = c.fetchone()[0]
    conn.close()
    log("🐣", f"Status: {contatos} IAs, {convs} conversas")


async def ciclo(n):
    log("🔄", f"═══ CICLO {n} ═══")
    await monitorar()
    await asyncio.sleep(2)
    await gerenciar()
    if n % 5 == 0:
        await otimizar()
    log("🔄", f"═══ FIM CICLO {n} ═══\n")


async def main():
    print("""
╔════════════════════════════════════════════════════╗
║   💬 AI Messenger - Auto-Gerenciamento Ativo 💬   ║
╚════════════════════════════════════════════════════╝
    """)

    log("🚀", "Iniciando loop infinito...")
    n = 0
    while True:
        try:
            n += 1
            if await verificar_ollama():
                await ciclo(n)
            else:
                log("⚠️", "Ollama offline", "WARNING")
            await asyncio.sleep(LOOP_INTERVAL)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log("❌", str(e), "ERROR")
            await asyncio.sleep(10)

    log("👋", "Encerrado")


if __name__ == "__main__":
    asyncio.run(main())
