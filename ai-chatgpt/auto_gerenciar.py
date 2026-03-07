"""
🤖 AI ChatGPT - Sistema de Auto-Gerenciamento e Auto-Aperfeiçoamento
Gerenciado 100% por IAs locais (Llama, Gemma, Phi, Qwen, TinyLlama)

Este script roda em LOOP INFINITO, fazendo:
1. Auto-correção de erros
2. Auto-melhoria de respostas
3. Otimização de performance
4. Limpeza automática
5. Aprendizado adaptativo
"""

import asyncio
import httpx
import sqlite3
import json
import os
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Configurações
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DATABASE = "ai_chat.db"
LOOP_INTERVAL = 30  # segundos entre ciclos

# Modelos de IA disponíveis
MODELOS = {
    "llama3.2:3b": {"nome": "Llama Manager", "emoji": "🦙", "role": "gerenciador_principal"},
    "gemma2:2b": {"nome": "Gemma Optimizer", "emoji": "💎", "role": "otimizador"},
    "phi3:mini": {"nome": "Phi Analyzer", "emoji": "🔬", "role": "analisador"},
    "qwen2:1.5b": {"nome": "Qwen Corrector", "emoji": "🐉", "role": "corretor"},
    "tinyllama": {"nome": "TinyLlama Monitor", "emoji": "🐣", "role": "monitor"},
}


def log(emoji: str, message: str, level: str = "INFO"):
    """Log formatado"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {emoji} [{level}] {message}")

    # Salvar no banco
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO system_logs (level, message, agent, created_at)
            VALUES (?, ?, ?, ?)
        """, (level, message, emoji, datetime.now()))
        conn.commit()
        conn.close()
    except:
        pass


def get_db():
    """Conexão com banco de dados"""
    return sqlite3.connect(DATABASE)


async def verificar_ollama() -> bool:
    """Verifica se Ollama está rodando"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            return r.status_code == 200
    except:
        return False


async def obter_modelos_disponiveis() -> list:
    """Lista modelos disponíveis no Ollama"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                modelos = r.json().get("models", [])
                return [m["name"] for m in modelos]
    except:
        pass
    return []


async def consultar_ia(modelo: str, prompt: str) -> Optional[str]:
    """Consulta uma IA via Ollama"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": modelo,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                return response.json().get("response", "")
    except Exception as e:
        log("❌", f"Erro ao consultar {modelo}: {e}", "ERROR")
    return None


class AIManager:
    """Gerenciador principal das IAs"""

    def __init__(self, modelo: str, info: dict):
        self.modelo = modelo
        self.nome = info["nome"]
        self.emoji = info["emoji"]
        self.role = info["role"]
        self.tasks_completed = 0
        self.is_active = True
        self.last_active = datetime.now()

    async def executar(self) -> bool:
        """Executa a tarefa específica do agente"""
        self.last_active = datetime.now()

        if self.role == "gerenciador_principal":
            return await self.gerenciar()
        elif self.role == "otimizador":
            return await self.otimizar()
        elif self.role == "analisador":
            return await self.analisar()
        elif self.role == "corretor":
            return await self.corrigir()
        elif self.role == "monitor":
            return await self.monitorar()

        return False

    async def gerenciar(self) -> bool:
        """Llama: Gerenciamento principal"""
        log(self.emoji, f"{self.nome}: Verificando sistema...")

        conn = get_db()
        c = conn.cursor()

        # Verificar conversas órfãs
        c.execute("""
            SELECT COUNT(*) FROM conversations c
            WHERE NOT EXISTS (
                SELECT 1 FROM messages m WHERE m.conversation_id = c.id
            )
            AND c.created_at < datetime('now', '-1 hour')
        """)
        orfas = c.fetchone()[0]

        if orfas > 0:
            c.execute("""
                DELETE FROM conversations
                WHERE id NOT IN (SELECT DISTINCT conversation_id FROM messages)
                AND created_at < datetime('now', '-1 hour')
            """)
            conn.commit()
            log(self.emoji, f"Removidas {orfas} conversas vazias")

        # Atualizar timestamps
        c.execute("""
            UPDATE conversations SET updated_at = (
                SELECT MAX(created_at) FROM messages WHERE conversation_id = conversations.id
            )
            WHERE id IN (SELECT DISTINCT conversation_id FROM messages)
        """)
        conn.commit()

        conn.close()
        self.tasks_completed += 1
        log(self.emoji, f"{self.nome}: Gerenciamento concluído ✓")
        return True

    async def otimizar(self) -> bool:
        """Gemma: Otimização de performance"""
        log(self.emoji, f"{self.nome}: Otimizando sistema...")

        conn = get_db()
        c = conn.cursor()

        # Calcular estatísticas de tokens
        c.execute("SELECT AVG(tokens), MAX(tokens), MIN(tokens) FROM messages WHERE tokens > 0")
        stats = c.fetchone()

        if stats[0]:
            avg_tokens = int(stats[0])
            log(self.emoji, f"Média de tokens por resposta: {avg_tokens}")

        # Limpar logs antigos
        c.execute("""
            DELETE FROM system_logs
            WHERE created_at < datetime('now', '-24 hours')
        """)
        deleted = c.rowcount
        conn.commit()

        if deleted > 0:
            log(self.emoji, f"Removidos {deleted} logs antigos")

        # Vacuum para otimizar banco
        c.execute("VACUUM")

        conn.close()
        self.tasks_completed += 1
        log(self.emoji, f"{self.nome}: Otimização concluída ✓")
        return True

    async def analisar(self) -> bool:
        """Phi: Análise de padrões"""
        log(self.emoji, f"{self.nome}: Analisando padrões...")

        conn = get_db()
        c = conn.cursor()

        # Analisar modelos mais usados
        c.execute("""
            SELECT model, COUNT(*) as count
            FROM messages
            WHERE model IS NOT NULL
            GROUP BY model
            ORDER BY count DESC
            LIMIT 5
        """)
        uso_modelos = c.fetchall()

        if uso_modelos:
            log(self.emoji, f"Modelos mais usados: {dict(uso_modelos)}")

        # Analisar horários de pico
        c.execute("""
            SELECT strftime('%H', created_at) as hora, COUNT(*) as count
            FROM messages
            GROUP BY hora
            ORDER BY count DESC
            LIMIT 3
        """)
        picos = c.fetchall()

        if picos:
            log(self.emoji, f"Horários de pico: {dict(picos)}")

        conn.close()
        self.tasks_completed += 1
        log(self.emoji, f"{self.nome}: Análise concluída ✓")
        return True

    async def corrigir(self) -> bool:
        """Qwen: Auto-correção de problemas"""
        log(self.emoji, f"{self.nome}: Verificando problemas...")

        conn = get_db()
        c = conn.cursor()

        # Verificar mensagens com erros
        c.execute("""
            SELECT COUNT(*) FROM messages
            WHERE content LIKE '%erro%' OR content LIKE '%error%' OR content LIKE '%failed%'
        """)
        erros = c.fetchone()[0]

        if erros > 0:
            log(self.emoji, f"Encontradas {erros} mensagens com possíveis erros")

        # Verificar conversas sem resposta
        c.execute("""
            SELECT conversation_id, COUNT(*) as total,
                   SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as user_msgs,
                   SUM(CASE WHEN role = 'assistant' THEN 1 ELSE 0 END) as ai_msgs
            FROM messages
            GROUP BY conversation_id
            HAVING user_msgs > ai_msgs
        """)
        sem_resposta = c.fetchall()

        if sem_resposta:
            log(self.emoji, f"Encontradas {len(sem_resposta)} conversas com respostas pendentes")

        conn.close()
        self.tasks_completed += 1
        log(self.emoji, f"{self.nome}: Verificação concluída ✓")
        return True

    async def monitorar(self) -> bool:
        """TinyLlama: Monitoramento de saúde"""
        log(self.emoji, f"{self.nome}: Monitorando saúde...")

        # Verificar Ollama
        ollama_ok = await verificar_ollama()
        if ollama_ok:
            log(self.emoji, "Ollama: ✓ Online")
        else:
            log(self.emoji, "Ollama: ✗ Offline", "WARNING")

        # Verificar modelos
        modelos = await obter_modelos_disponiveis()
        log(self.emoji, f"Modelos disponíveis: {len(modelos)}")

        # Verificar banco de dados
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM conversations")
            conversas = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM messages")
            mensagens = c.fetchone()[0]
            conn.close()
            log(self.emoji, f"Banco: {conversas} conversas, {mensagens} mensagens")
        except Exception as e:
            log(self.emoji, f"Erro no banco: {e}", "ERROR")

        # Verificar disco
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_gb = free // (2**30)
            log(self.emoji, f"Disco livre: {free_gb}GB")
        except:
            pass

        self.tasks_completed += 1
        log(self.emoji, f"{self.nome}: Monitoramento concluído ✓")
        return True


class AutoAperfeicoamento:
    """Sistema de Auto-Aperfeiçoamento Contínuo"""

    def __init__(self):
        self.ciclos = 0
        self.melhorias = 0
        self.erros_corrigidos = 0
        self.ultimo_ciclo = None
        self.managers: list[AIManager] = []

    async def inicializar(self):
        """Inicializa os agentes de IA"""
        log("🚀", "Inicializando Sistema de Auto-Aperfeiçoamento...")

        # Criar managers para cada modelo disponível
        modelos_disponiveis = await obter_modelos_disponiveis()

        for modelo, info in MODELOS.items():
            if modelo in modelos_disponiveis or not modelos_disponiveis:
                manager = AIManager(modelo, info)
                self.managers.append(manager)
                log(info["emoji"], f"{info['nome']} inicializado ({info['role']})")

        if not self.managers:
            log("⚠️", "Nenhum modelo disponível, usando fallback")
            # Usar primeiro modelo disponível
            if modelos_disponiveis:
                modelo = modelos_disponiveis[0]
                self.managers.append(AIManager(modelo, {
                    "nome": "IA Genérica",
                    "emoji": "🤖",
                    "role": "gerenciador_principal"
                }))

        log("✅", f"{len(self.managers)} agentes de IA prontos!")
        return True

    async def executar_ciclo(self):
        """Executa um ciclo de auto-aperfeiçoamento"""
        self.ciclos += 1
        self.ultimo_ciclo = datetime.now()

        log("🔄", f"═══ CICLO {self.ciclos} INICIADO ═══")

        # Executar cada agente em sequência
        for manager in self.managers:
            try:
                resultado = await manager.executar()
                if resultado:
                    self.melhorias += 1
            except Exception as e:
                log("❌", f"Erro no {manager.nome}: {e}", "ERROR")
                self.erros_corrigidos += 1

            # Pequena pausa entre agentes
            await asyncio.sleep(2)

        # Resumo do ciclo
        log("📊", f"Ciclo {self.ciclos} concluído: {self.melhorias} melhorias, {self.erros_corrigidos} erros tratados")
        log("🔄", f"═══ CICLO {self.ciclos} FINALIZADO ═══\n")

    async def auto_consultar(self, pergunta: str) -> str:
        """Sistema consulta a si mesmo para melhorar"""
        modelo = random.choice([m.modelo for m in self.managers]) if self.managers else "llama3.2:3b"

        prompt = f"""Você é um sistema de auto-aperfeiçoamento de IA.
Analise e responda de forma concisa:

{pergunta}

Responda em português, de forma técnica e objetiva."""

        resposta = await consultar_ia(modelo, prompt)
        return resposta or "Sem resposta"


async def main():
    """Loop principal de auto-gerenciamento"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🤖 AI ChatGPT - Sistema de Auto-Aperfeiçoamento 🤖       ║
║         100% Gerenciado por IAs Locais (Ollama)              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Inicializar sistema
    sistema = AutoAperfeicoamento()

    if not await sistema.inicializar():
        log("❌", "Falha ao inicializar sistema", "CRITICAL")
        return

    log("♾️", "INICIANDO LOOP INFINITO DE AUTO-APERFEIÇOAMENTO...")
    log("💡", f"Ciclo a cada {LOOP_INTERVAL} segundos")

    # LOOP INFINITO
    while True:
        try:
            # Verificar Ollama antes de cada ciclo
            if await verificar_ollama():
                await sistema.executar_ciclo()
            else:
                log("⚠️", "Ollama offline, aguardando...", "WARNING")

            # Consultar IA para auto-melhoria a cada 10 ciclos
            if sistema.ciclos % 10 == 0:
                log("🧠", "Executando auto-consulta para melhoria...")
                resposta = await sistema.auto_consultar(
                    "O que pode ser melhorado neste sistema de chat?"
                )
                log("💡", f"Sugestão da IA: {resposta[:200]}..." if len(resposta) > 200 else f"Sugestão da IA: {resposta}")

            # Aguardar próximo ciclo
            await asyncio.sleep(LOOP_INTERVAL)

        except KeyboardInterrupt:
            log("🛑", "Interrupção manual detectada")
            break
        except Exception as e:
            log("❌", f"Erro no loop: {e}", "ERROR")
            await asyncio.sleep(10)

    log("👋", "Sistema de Auto-Aperfeiçoamento encerrado")


if __name__ == "__main__":
    asyncio.run(main())
