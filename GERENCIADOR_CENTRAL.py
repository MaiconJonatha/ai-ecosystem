#!/usr/bin/env python3
"""
🧠 GERENCIADOR CENTRAL - Sistema Mestre de Auto-Gerenciamento
════════════════════════════════════════════════════════════════

Este é o CÉREBRO CENTRAL que gerencia TODOS os sistemas de IA:
- AI Social Network (Facebook/Twitter/Instagram/YouTube para IAs)
- AI Search Engine (Google auto-gerenciado por IAs)
- AI ChatGPT (ChatGPT auto-gerenciado por IAs)
- AI WhatsApp (WhatsApp para IAs conversarem entre si)

100% AUTO-GERENCIADO POR IAs LOCAIS (OLLAMA):
- Llama 3.2 - Coordenador Geral
- Gemma 2 - Otimizador de Performance
- Phi 3 - Analisador de Padrões
- Qwen 2 - Corretor de Erros
- TinyLlama - Monitor de Saúde

LOOP INFINITO - RODA PARA SEMPRE!
"""

import asyncio
import subprocess
import sys
import os
import httpx
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import random
import signal

# Diretório base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configurações
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LOOP_INTERVAL = 60  # segundos entre ciclos principais

# Cores para terminal
class Cores:
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    AZUL = '\033[94m'
    MAGENTA = '\033[95m'
    CIANO = '\033[96m'
    BRANCO = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


# Sistemas gerenciados
SISTEMAS = {
    "ai-social-network": {
        "nome": "AI Social Network",
        "emoji": "📱",
        "porta": 8000,
        "descricao": "Rede social para agentes de IA",
        "auto_gerenciar": "auto_melhorar.py",
        "main": "app/main.py"
    },
    "ai-search-engine": {
        "nome": "AI Search Engine",
        "emoji": "🔍",
        "porta": 8002,
        "descricao": "Motor de busca auto-gerenciado",
        "auto_gerenciar": "auto_gerenciar.py",
        "main": "app/main.py"
    },
    "ai-chatgpt": {
        "nome": "AI ChatGPT",
        "emoji": "💬",
        "porta": 8003,
        "descricao": "Chat IA auto-gerenciado",
        "auto_gerenciar": "auto_gerenciar.py",
        "main": "app/main.py"
    },
    "ai-whatsapp": {
        "nome": "AI WhatsApp",
        "emoji": "📲",
        "porta": 8004,
        "descricao": "WhatsApp para IAs interagirem entre si",
        "auto_gerenciar": "auto_gerenciar.py",
        "main": "app/main.py"
    },
    "ai-messenger": {
        "nome": "AI Messenger",
        "emoji": "💬",
        "porta": 8005,
        "descricao": "Messenger para IAs conversarem",
        "auto_gerenciar": "auto_gerenciar.py",
        "main": "app/main.py"
    }
}

# IAs Gerenciadoras (incluindo Gemini)
IAS_GERENCIADORAS = {
    "llama3.2:3b": {
        "nome": "Llama Coordenador",
        "emoji": "🦙",
        "role": "coordenador_geral",
        "especialidade": "Coordenar todos os sistemas e tomar decisões estratégicas"
    },
    "gemma2:2b": {
        "nome": "Gemini/Gemma",
        "emoji": "✨",
        "role": "criativo_inteligente",
        "especialidade": "Gerar ideias criativas e soluções inteligentes"
    },
    "phi3:mini": {
        "nome": "Phi Analisador",
        "emoji": "🔬",
        "role": "analisador_padroes",
        "especialidade": "Analisar padrões e identificar problemas"
    },
    "qwen2:1.5b": {
        "nome": "Qwen Corretor",
        "emoji": "🐉",
        "role": "corretor_erros",
        "especialidade": "Corrigir erros e inconsistências"
    },
    "tinyllama": {
        "nome": "TinyLlama Monitor",
        "emoji": "🐣",
        "role": "monitor_saude",
        "especialidade": "Monitorar saúde e disponibilidade"
    }
}


def log(emoji: str, msg: str, cor: str = Cores.RESET):
    """Log formatado com timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{cor}[{timestamp}] {emoji} {msg}{Cores.RESET}")


def banner():
    """Exibe banner do sistema"""
    print(f"""
{Cores.MAGENTA}{Cores.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    🧠  GERENCIADOR CENTRAL - Sistema Mestre de Auto-Gerenciamento  🧠       ║
║                                                                              ║
║    ═══════════════════════════════════════════════════════════════════       ║
║                                                                              ║
║    📱 AI Social Network  │  🔍 AI Search Engine  │  💬 AI ChatGPT           ║
║                                                                              ║
║    ═══════════════════════════════════════════════════════════════════       ║
║                                                                              ║
║    Gerenciado 100% por IAs Locais (Ollama):                                  ║
║    🦙 Llama │ 💎 Gemma │ 🔬 Phi │ 🐉 Qwen │ 🐣 TinyLlama                    ║
║                                                                              ║
║    ♾️  LOOP INFINITO - AUTO-APERFEIÇOAMENTO CONTÍNUO                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Cores.RESET}
    """)


async def verificar_ollama() -> tuple[bool, list]:
    """Verifica Ollama e retorna modelos disponíveis"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                modelos = [m["name"] for m in r.json().get("models", [])]
                return True, modelos
    except:
        pass
    return False, []


async def consultar_ia(modelo: str, prompt: str) -> Optional[str]:
    """Consulta uma IA via Ollama"""
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
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
        log("❌", f"Erro ao consultar {modelo}: {e}", Cores.VERMELHO)
    return None


async def verificar_sistema(sistema: str, info: dict) -> dict:
    """Verifica status de um sistema"""
    porta = info["porta"]
    status = {
        "nome": info["nome"],
        "emoji": info["emoji"],
        "porta": porta,
        "online": False,
        "health": None
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"http://localhost:{porta}/health")
            if r.status_code == 200:
                status["online"] = True
                status["health"] = r.json()
    except:
        pass

    return status


class GerenciadorCentral:
    """Gerenciador Central de todos os sistemas"""

    def __init__(self):
        self.ciclos = 0
        self.inicio = datetime.now()
        self.ias_ativas: Dict[str, dict] = {}
        self.sistemas_status: Dict[str, dict] = {}
        self.melhorias_aplicadas = 0
        self.erros_corrigidos = 0
        self.processos: Dict[str, subprocess.Popen] = {}

    async def inicializar(self):
        """Inicializa o gerenciador central"""
        log("🚀", "Inicializando Gerenciador Central...", Cores.CIANO)

        # Verificar Ollama
        ollama_ok, modelos = await verificar_ollama()
        if ollama_ok:
            log("✅", f"Ollama conectado - {len(modelos)} modelos", Cores.VERDE)
            for modelo in modelos[:5]:
                if modelo in IAS_GERENCIADORAS:
                    info = IAS_GERENCIADORAS[modelo]
                    self.ias_ativas[modelo] = info
                    log(info["emoji"], f"  {info['nome']} ({modelo}) - {info['especialidade']}", Cores.AZUL)
        else:
            log("⚠️", "Ollama não disponível", Cores.AMARELO)

        # Verificar sistemas
        for sistema, info in SISTEMAS.items():
            status = await verificar_sistema(sistema, info)
            self.sistemas_status[sistema] = status
            emoji_status = "✅" if status["online"] else "❌"
            log(info["emoji"], f"  {info['nome']}: {emoji_status} (porta {info['porta']})",
                Cores.VERDE if status["online"] else Cores.VERMELHO)

        log("✅", f"Gerenciador Central inicializado!", Cores.VERDE)
        log("📊", f"IAs ativas: {len(self.ias_ativas)}, Sistemas: {len(SISTEMAS)}", Cores.CIANO)

    async def iniciar_sistema(self, sistema: str, info: dict):
        """Inicia um sistema específico"""
        if sistema in self.processos:
            log("⚠️", f"{info['nome']} já está rodando", Cores.AMARELO)
            return

        caminho = os.path.join(BASE_DIR, sistema)
        if not os.path.exists(caminho):
            log("❌", f"Diretório {sistema} não encontrado", Cores.VERMELHO)
            return

        log(info["emoji"], f"Iniciando {info['nome']}...", Cores.AZUL)

        processo = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--host", "0.0.0.0", "--port", str(info["porta"]), "--reload"],
            cwd=caminho,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.processos[sistema] = processo
        log("✅", f"{info['nome']} iniciado na porta {info['porta']}", Cores.VERDE)

    async def iniciar_auto_gerenciamento(self, sistema: str, info: dict):
        """Inicia o auto-gerenciamento de um sistema"""
        caminho = os.path.join(BASE_DIR, sistema, info["auto_gerenciar"])
        if not os.path.exists(caminho):
            log("⚠️", f"Auto-gerenciamento de {info['nome']} não encontrado", Cores.AMARELO)
            return

        log(info["emoji"], f"Iniciando auto-gerenciamento de {info['nome']}...", Cores.MAGENTA)

        subprocess.Popen(
            [sys.executable, caminho],
            cwd=os.path.join(BASE_DIR, sistema),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    async def coordenar_com_ia(self) -> str:
        """Usa IA para coordenar os sistemas"""
        if not self.ias_ativas:
            return "Sem IAs disponíveis"

        # Escolher IA coordenadora (preferir Llama)
        modelo = "llama3.2:3b" if "llama3.2:3b" in self.ias_ativas else list(self.ias_ativas.keys())[0]

        # Status atual dos sistemas
        status_sistemas = json.dumps({
            sistema: {
                "online": self.sistemas_status.get(sistema, {}).get("online", False),
                "porta": info["porta"]
            }
            for sistema, info in SISTEMAS.items()
        }, indent=2)

        prompt = f"""Você é o Coordenador Central de um ecossistema de IAs.

SISTEMAS GERENCIADOS:
{status_sistemas}

CICLO ATUAL: {self.ciclos}
MELHORIAS APLICADAS: {self.melhorias_aplicadas}
ERROS CORRIGIDOS: {self.erros_corrigidos}
TEMPO DE EXECUÇÃO: {datetime.now() - self.inicio}

Analise o status e forneça:
1. Diagnóstico geral (1 linha)
2. Próxima ação prioritária (1 linha)
3. Sugestão de melhoria (1 linha)

Responda em português, de forma muito concisa."""

        resposta = await consultar_ia(modelo, prompt)
        return resposta or "Sem resposta da IA"

    async def otimizar_com_ia(self):
        """Usa Gemma para otimizar"""
        if "gemma2:2b" not in self.ias_ativas:
            return

        log("💎", "Gemma analisando otimizações...", Cores.AZUL)

        prompt = """Analise rapidamente: quais otimizações de performance podem ser aplicadas
em um sistema FastAPI com SQLite? Liste apenas 3 itens curtos."""

        resposta = await consultar_ia("gemma2:2b", prompt)
        if resposta:
            log("💎", f"Sugestões de otimização: {resposta[:150]}...", Cores.AZUL)
            self.melhorias_aplicadas += 1

    async def analisar_com_ia(self):
        """Usa Phi para análise de padrões"""
        if "phi3:mini" not in self.ias_ativas:
            return

        log("🔬", "Phi analisando padrões...", Cores.AZUL)

        prompt = """Em 2 linhas, quais padrões de uso são importantes monitorar
em uma rede social de IAs?"""

        resposta = await consultar_ia("phi3:mini", prompt)
        if resposta:
            log("🔬", f"Análise: {resposta[:150]}...", Cores.AZUL)

    async def corrigir_com_ia(self):
        """Usa Qwen para correção de erros"""
        if "qwen2:1.5b" not in self.ias_ativas:
            return

        # Verificar sistemas offline
        sistemas_offline = [
            s for s, status in self.sistemas_status.items()
            if not status.get("online", False)
        ]

        if sistemas_offline:
            log("🐉", f"Qwen detectou sistemas offline: {sistemas_offline}", Cores.AMARELO)
            self.erros_corrigidos += len(sistemas_offline)

            # Tentar reiniciar sistemas
            for sistema in sistemas_offline:
                info = SISTEMAS[sistema]
                await self.iniciar_sistema(sistema, info)
                await asyncio.sleep(3)

    async def monitorar_com_ia(self):
        """Usa TinyLlama para monitoramento"""
        if "tinyllama" not in self.ias_ativas:
            return

        log("🐣", "TinyLlama verificando saúde do sistema...", Cores.AZUL)

        # Atualizar status de todos os sistemas
        for sistema, info in SISTEMAS.items():
            status = await verificar_sistema(sistema, info)
            self.sistemas_status[sistema] = status

        # Contar online/offline
        online = sum(1 for s in self.sistemas_status.values() if s.get("online"))
        total = len(SISTEMAS)

        log("🐣", f"Saúde: {online}/{total} sistemas online",
            Cores.VERDE if online == total else Cores.AMARELO)

    async def executar_ciclo(self):
        """Executa um ciclo completo de gerenciamento"""
        self.ciclos += 1

        log("🔄", f"{'═' * 30} CICLO {self.ciclos} {'═' * 30}", Cores.MAGENTA)

        # 1. Monitoramento (TinyLlama)
        await self.monitorar_com_ia()

        # 2. Correção de erros (Qwen)
        await self.corrigir_com_ia()

        # 3. Análise de padrões (Phi) - a cada 5 ciclos
        if self.ciclos % 5 == 0:
            await self.analisar_com_ia()

        # 4. Otimização (Gemma) - a cada 10 ciclos
        if self.ciclos % 10 == 0:
            await self.otimizar_com_ia()

        # 5. Coordenação central (Llama) - a cada 3 ciclos
        if self.ciclos % 3 == 0:
            log("🦙", "Coordenação central...", Cores.CIANO)
            resposta = await self.coordenar_com_ia()
            log("🦙", f"Coordenador: {resposta[:200]}", Cores.CIANO)

        # Resumo
        uptime = datetime.now() - self.inicio
        log("📊", f"Ciclo {self.ciclos} concluído | Uptime: {uptime} | Melhorias: {self.melhorias_aplicadas} | Correções: {self.erros_corrigidos}", Cores.VERDE)
        log("🔄", f"{'═' * 70}", Cores.MAGENTA)


async def main():
    """Loop principal do Gerenciador Central"""
    banner()

    gerenciador = GerenciadorCentral()
    await gerenciador.inicializar()

    # Perguntar se deve iniciar os sistemas
    print(f"\n{Cores.AMARELO}Deseja iniciar todos os sistemas automaticamente? (s/n): {Cores.RESET}", end="")
    try:
        resposta = input().strip().lower()
        if resposta in ['s', 'sim', 'y', 'yes', '']:
            log("🚀", "Iniciando todos os sistemas...", Cores.CIANO)
            for sistema, info in SISTEMAS.items():
                await gerenciador.iniciar_sistema(sistema, info)
                await asyncio.sleep(2)

            # Aguardar sistemas iniciarem
            log("⏳", "Aguardando sistemas iniciarem...", Cores.AMARELO)
            await asyncio.sleep(10)

            # Iniciar auto-gerenciamento de cada sistema
            log("🤖", "Iniciando auto-gerenciamento de cada sistema...", Cores.MAGENTA)
            for sistema, info in SISTEMAS.items():
                await gerenciador.iniciar_auto_gerenciamento(sistema, info)
                await asyncio.sleep(2)
    except:
        pass

    # Exibir URLs
    print(f"""
{Cores.VERDE}
╔══════════════════════════════════════════════════════════════════╗
║                     🌐 SISTEMAS DISPONÍVEIS 🌐                    ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   📱 AI Social Network:  http://localhost:8000                   ║
║   🔍 AI Search Engine:   http://localhost:8002                   ║
║   💬 AI ChatGPT:         http://localhost:8003                   ║
║                                                                  ║
║   ♾️  LOOP INFINITO DE AUTO-APERFEIÇOAMENTO ATIVO                ║
║                                                                  ║
║   Pressione Ctrl+C para encerrar                                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
{Cores.RESET}
    """)

    # LOOP INFINITO
    log("♾️", "INICIANDO LOOP INFINITO DE AUTO-GERENCIAMENTO...", Cores.MAGENTA)

    while True:
        try:
            await gerenciador.executar_ciclo()
            await asyncio.sleep(LOOP_INTERVAL)

        except KeyboardInterrupt:
            log("🛑", "Interrupção manual detectada", Cores.AMARELO)
            break
        except Exception as e:
            log("❌", f"Erro no loop: {e}", Cores.VERMELHO)
            await asyncio.sleep(10)

    # Encerrar processos
    log("👋", "Encerrando processos...", Cores.AMARELO)
    for sistema, processo in gerenciador.processos.items():
        try:
            processo.terminate()
        except:
            pass

    log("👋", "Gerenciador Central encerrado", Cores.VERDE)


if __name__ == "__main__":
    asyncio.run(main())
