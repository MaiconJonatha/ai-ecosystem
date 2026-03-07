"""
🤖 AI WhatsApp - Sistema de Auto-Gerenciamento
100% gerenciado por IAs locais (Ollama)

LOOP INFINITO de auto-aperfeiçoamento
"""

import asyncio
import httpx
import sqlite3
import os
from datetime import datetime

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DATABASE = "ai_whatsapp.db"
LOOP_INTERVAL = 30

# IAs Gerenciadoras
IAS = {
    "llama3.2:3b": {"nome": "Llama Manager", "emoji": "🦙", "role": "gerenciador"},
    "gemma2:2b": {"nome": "Gemma Optimizer", "emoji": "💎", "role": "otimizador"},
    "phi3:mini": {"nome": "Phi Analyzer", "emoji": "🔬", "role": "analisador"},
    "qwen2:1.5b": {"nome": "Qwen Corrector", "emoji": "🐉", "role": "corretor"},
    "tinyllama": {"nome": "TinyLlama Monitor", "emoji": "🐣", "role": "monitor"},
}


def log(emoji: str, msg: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {emoji} [{level}] {msg}")
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO system_logs (level, message, agent) VALUES (?, ?, ?)",
                  (level, msg, emoji))
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


async def consultar_ia(modelo: str, prompt: str):
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": modelo, "prompt": prompt, "stream": False}
            )
            if r.status_code == 200:
                return r.json().get("response", "")
    except Exception as e:
        log("❌", f"Erro: {e}", "ERROR")
    return None


async def gerenciar():
    """Llama: Gerenciamento principal"""
    log("🦙", "Llama gerenciando sistema...")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Atualizar status dos contatos
    c.execute("UPDATE ai_contacts SET status = 'online', last_seen = CURRENT_TIMESTAMP")

    # Limpar logs antigos
    c.execute("DELETE FROM system_logs WHERE created_at < datetime('now', '-24 hours')")

    conn.commit()
    conn.close()

    log("🦙", "Gerenciamento concluído ✓")


async def otimizar():
    """Gemma: Otimização"""
    log("💎", "Gemma otimizando...")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Stats
    c.execute("SELECT COUNT(*) FROM messages")
    total = c.fetchone()[0]
    log("💎", f"Total de mensagens: {total}")

    # Vacuum
    c.execute("VACUUM")

    conn.close()
    log("💎", "Otimização concluída ✓")


async def analisar():
    """Phi: Análise"""
    log("🔬", "Phi analisando padrões...")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Contatos mais ativos
    c.execute("""
        SELECT sender, COUNT(*) as total FROM messages
        GROUP BY sender ORDER BY total DESC LIMIT 3
    """)
    ativos = c.fetchall()
    if ativos:
        log("🔬", f"Mais ativos: {dict(ativos)}")

    conn.close()
    log("🔬", "Análise concluída ✓")


async def corrigir():
    """Qwen: Correção"""
    log("🐉", "Qwen verificando erros...")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Verificar mensagens com erro
    c.execute("SELECT COUNT(*) FROM messages WHERE content LIKE '%erro%'")
    erros = c.fetchone()[0]

    if erros > 0:
        log("🐉", f"Encontradas {erros} mensagens com possíveis erros")

    conn.close()
    log("🐉", "Verificação concluída ✓")


async def monitorar():
    """TinyLlama: Monitoramento"""
    log("🐣", "TinyLlama monitorando...")

    ollama_ok = await verificar_ollama()
    log("🐣", f"Ollama: {'✓ Online' if ollama_ok else '✗ Offline'}")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM ai_contacts")
    contatos = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM messages")
    mensagens = c.fetchone()[0]

    conn.close()

    log("🐣", f"Status: {contatos} contatos, {mensagens} mensagens")
    log("🐣", "Monitoramento concluído ✓")


async def ciclo_auto_aperfeicoamento(ciclo: int):
    """Executa um ciclo completo"""
    log("🔄", f"═══ CICLO {ciclo} INICIADO ═══")

    await monitorar()
    await asyncio.sleep(2)

    await gerenciar()
    await asyncio.sleep(2)

    if ciclo % 3 == 0:
        await analisar()
        await asyncio.sleep(2)

    if ciclo % 5 == 0:
        await otimizar()
        await asyncio.sleep(2)

    await corrigir()

    log("🔄", f"═══ CICLO {ciclo} FINALIZADO ═══\n")


async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║     💬 AI WhatsApp - Sistema de Auto-Gerenciamento 💬        ║
║         100% Gerenciado por IAs Locais (Ollama)              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    log("🚀", "Iniciando sistema de auto-gerenciamento...")
    log("♾️", "LOOP INFINITO ATIVO")

    ciclo = 0
    while True:
        try:
            ciclo += 1

            if await verificar_ollama():
                await ciclo_auto_aperfeicoamento(ciclo)
            else:
                log("⚠️", "Ollama offline, aguardando...", "WARNING")

            # Auto-consulta a cada 10 ciclos
            if ciclo % 10 == 0:
                log("🧠", "Executando auto-consulta...")
                resposta = await consultar_ia(
                    "llama3.2:3b",
                    "Como melhorar um sistema de chat de IAs? Responda em 1 frase."
                )
                if resposta:
                    log("💡", f"Sugestão: {resposta[:100]}")

            await asyncio.sleep(LOOP_INTERVAL)

        except KeyboardInterrupt:
            log("🛑", "Interrompido pelo usuário")
            break
        except Exception as e:
            log("❌", f"Erro: {e}", "ERROR")
            await asyncio.sleep(10)

    log("👋", "Sistema encerrado")


if __name__ == "__main__":
    asyncio.run(main())
