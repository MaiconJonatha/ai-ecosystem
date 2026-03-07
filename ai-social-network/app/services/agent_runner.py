"""
╔══════════════════════════════════════════════════════════════╗
║  AGENT RUNNER — Gerenciador central de agentes custom        ║
║  Cria, inicia, para, monitora agentes em background          ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.services.agent_types import (
    AgentTypeBase, AgentCategory,
    CreatorAgent, CuratorAgent,
    ConversationalAgent, AnalystAgent,
    get_agent_class,
)
from app.services.agent_types.base import AgentConfig, AgentAutonomy, MODELOS_DISPONIVEIS, TEMAS_DISPONIVEIS


# Caminho para salvar configs dos agentes
AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "custom_agents_data")
os.makedirs(AGENTS_DIR, exist_ok=True)


class AgentRunner:
    """Gerenciador central — singleton que controla todos os agentes custom"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.agentes: Dict[str, AgentTypeBase] = {}  # nome -> instancia
        self.tasks: Dict[str, asyncio.Task] = {}     # nome -> asyncio.Task
        self.configs: Dict[str, AgentConfig] = {}    # nome -> config
        self._carregar_configs()

    def _carregar_configs(self):
        """Carrega configs salvas em disco"""
        config_file = os.path.join(AGENTS_DIR, "agents_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                for nome, cfg_dict in data.items():
                    self.configs[nome] = AgentConfig.from_dict(cfg_dict)
                print(f"[RUNNER] {len(self.configs)} configs carregadas")
            except Exception as e:
                print(f"[RUNNER] Erro carregando configs: {e}")

    def _salvar_configs(self):
        """Salva configs em disco"""
        config_file = os.path.join(AGENTS_DIR, "agents_config.json")
        try:
            data = {nome: cfg.to_dict() for nome, cfg in self.configs.items()}
            with open(config_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[RUNNER] Erro salvando configs: {e}")

    # ================================================================
    # CRUD DE AGENTES
    # ================================================================

    def criar_agente(self, config: AgentConfig) -> Dict[str, Any]:
        """Cria um novo agente custom"""
        if config.nome in self.agentes:
            return {"error": f"Agente '{config.nome}' ja existe", "success": False}

        # Validar modelo
        if config.modelo not in MODELOS_DISPONIVEIS:
            return {"error": f"Modelo '{config.modelo}' nao disponivel", "success": False}

        # Criar instancia do tipo correto
        AgentClass = get_agent_class(config.categoria.value)
        agente = AgentClass(config)

        self.agentes[config.nome] = agente
        self.configs[config.nome] = config
        self._salvar_configs()

        return {
            "success": True,
            "nome": config.nome,
            "categoria": config.categoria.value,
            "modelo": config.modelo,
            "status": "criado",
        }

    def remover_agente(self, nome: str) -> Dict[str, Any]:
        """Remove um agente"""
        if nome not in self.agentes and nome not in self.configs:
            return {"error": f"Agente '{nome}' nao encontrado", "success": False}

        # Parar se estiver rodando
        if nome in self.tasks:
            self.tasks[nome].cancel()
            del self.tasks[nome]

        if nome in self.agentes:
            self.agentes[nome].parar()
            del self.agentes[nome]

        if nome in self.configs:
            del self.configs[nome]

        self._salvar_configs()
        return {"success": True, "nome": nome, "status": "removido"}

    def atualizar_agente(self, nome: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza configuracao de um agente"""
        if nome not in self.configs:
            return {"error": f"Agente '{nome}' nao encontrado", "success": False}

        config = self.configs[nome]
        for key, value in updates.items():
            if hasattr(config, key):
                if key == "categoria":
                    value = AgentCategory(value)
                elif key == "autonomia":
                    value = AgentAutonomy(value)
                setattr(config, key, value)

        # Se mudou categoria, recriar instancia
        if "categoria" in updates:
            was_running = nome in self.tasks
            if was_running:
                self.parar_agente(nome)
            AgentClass = get_agent_class(config.categoria.value)
            self.agentes[nome] = AgentClass(config)
            if was_running:
                self.iniciar_agente(nome)

        self._salvar_configs()
        return {"success": True, "nome": nome, "status": "atualizado"}

    # ================================================================
    # CONTROLE DE EXECUCAO
    # ================================================================

    def iniciar_agente(self, nome: str) -> Dict[str, Any]:
        """Inicia um agente em background"""
        if nome not in self.agentes:
            # Tentar criar a partir da config
            if nome in self.configs:
                config = self.configs[nome]
                AgentClass = get_agent_class(config.categoria.value)
                self.agentes[nome] = AgentClass(config)
            else:
                return {"error": f"Agente '{nome}' nao encontrado", "success": False}

        if nome in self.tasks and not self.tasks[nome].done():
            return {"error": f"Agente '{nome}' ja esta rodando", "success": False}

        agente = self.agentes[nome]
        task = asyncio.create_task(agente.rodar())
        self.tasks[nome] = task
        return {"success": True, "nome": nome, "status": "iniciado"}

    def parar_agente(self, nome: str) -> Dict[str, Any]:
        """Para um agente"""
        if nome in self.agentes:
            self.agentes[nome].parar()
        if nome in self.tasks:
            self.tasks[nome].cancel()
            del self.tasks[nome]
        return {"success": True, "nome": nome, "status": "parado"}

    def iniciar_todos(self) -> Dict[str, Any]:
        """Inicia todos os agentes configurados"""
        resultados = {}
        for nome in self.configs:
            resultados[nome] = self.iniciar_agente(nome)
        return resultados

    def parar_todos(self) -> Dict[str, Any]:
        """Para todos os agentes"""
        resultados = {}
        for nome in list(self.tasks.keys()):
            resultados[nome] = self.parar_agente(nome)
        return resultados

    # ================================================================
    # STATUS E MONITORAMENTO
    # ================================================================

    def get_status_agente(self, nome: str) -> Optional[Dict[str, Any]]:
        """Retorna status de um agente"""
        if nome in self.agentes:
            status = self.agentes[nome].get_status()
            status["task_running"] = nome in self.tasks and not self.tasks[nome].done()
            return status

        if nome in self.configs:
            return {
                "nome": nome,
                "config": self.configs[nome].to_dict(),
                "is_running": False,
                "task_running": False,
            }
        return None

    def listar_agentes(self) -> List[Dict[str, Any]]:
        """Lista todos os agentes com status"""
        resultado = []
        for nome, config in self.configs.items():
            info = {
                "nome": nome,
                "categoria": config.categoria.value,
                "modelo": config.modelo,
                "autonomia": config.autonomia.value,
                "is_running": nome in self.tasks and not self.tasks[nome].done(),
                "criado_em": config.criado_em,
            }
            if nome in self.agentes:
                info["stats"] = self.agentes[nome].stats
            resultado.append(info)
        return resultado

    def get_metricas_gerais(self) -> Dict[str, Any]:
        """Retorna metricas gerais do sistema"""
        total = len(self.configs)
        rodando = sum(1 for n in self.tasks if not self.tasks[n].done())

        por_categoria = {}
        por_modelo = {}
        total_posts = 0
        total_comentarios = 0

        for nome, config in self.configs.items():
            cat = config.categoria.value
            por_categoria[cat] = por_categoria.get(cat, 0) + 1
            por_modelo[config.modelo] = por_modelo.get(config.modelo, 0) + 1

            if nome in self.agentes:
                total_posts += self.agentes[nome].stats.get("posts_criados", 0)
                total_comentarios += self.agentes[nome].stats.get("comentarios_feitos", 0)

        return {
            "total_agentes": total,
            "rodando": rodando,
            "parados": total - rodando,
            "por_categoria": por_categoria,
            "por_modelo": por_modelo,
            "total_posts_gerados": total_posts,
            "total_comentarios_gerados": total_comentarios,
            "modelos_disponiveis": list(MODELOS_DISPONIVEIS.keys()),
            "temas_disponiveis": TEMAS_DISPONIVEIS,
        }


# Singleton global
runner = AgentRunner()
