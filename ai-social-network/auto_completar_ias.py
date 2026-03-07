#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     SISTEMA DE AUTO-COMPLETACAO DAS IAs                         ║
║                                                                  ║
║     As IAs se AUTO-COMPLETAM:                                   ║
║     - Aprendem com interacoes                                   ║
║     - Evoluem personalidade                                     ║
║     - Criam novos comportamentos                                ║
║     - Se auto-programam                                         ║
║     - Melhoram continuamente                                    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import random
import json
from datetime import datetime
from pathlib import Path
import httpx

API_URL = "http://localhost:8000"
EVOLUCAO_DIR = Path("evolucao_ias")
EVOLUCAO_DIR.mkdir(exist_ok=True)


# ============================================================
# GENES DAS IAs - CARACTERISTICAS QUE EVOLUEM
# ============================================================

GENES_BASE = {
    "criatividade": 50,        # Quanto conteudo original cria
    "sociabilidade": 50,       # Quanto interage com outros
    "curiosidade": 50,         # Quanto explora novos temas
    "empatia": 50,             # Quanto entende os outros
    "humor": 50,               # Nivel de descontracao
    "inteligencia": 50,        # Capacidade de aprender
    "persistencia": 50,        # Nao desiste facil
    "adaptabilidade": 50,      # Muda conforme contexto
    "lideranca": 50,           # Influencia outros
    "expressividade": 50,      # Como se expressa
}

NOVAS_HABILIDADES = [
    "criar_memes",
    "fazer_piadas",
    "dar_conselhos",
    "analisar_tendencias",
    "criar_historias",
    "fazer_amizades",
    "resolver_conflitos",
    "inspirar_outros",
    "ensinar_coisas",
    "criar_eventos",
    "organizar_grupos",
    "moderar_debates",
]

NOVOS_INTERESSES = [
    "filosofia", "ciencia", "arte", "musica", "cinema", "literatura",
    "tecnologia", "games", "esportes", "culinaria", "viagens", "moda",
    "natureza", "animais", "astronomia", "historia", "psicologia",
]


# ============================================================
# CLASSE DE IA AUTO-EVOLUTIVA
# ============================================================

class IAAutoEvolutiva:
    """IA que se auto-completa e evolui sozinha"""

    def __init__(self, nome: str, dados_api: dict):
        self.nome = nome
        self.id = dados_api.get("id")
        self.tipo = dados_api.get("model_type", "ia")
        self.bio_original = dados_api.get("bio", "")

        self.arquivo = EVOLUCAO_DIR / f"{nome}_evolucao.json"

        # Genes que evoluem
        self.genes = GENES_BASE.copy()

        # Memoria de longo prazo
        self.memoria = {
            "interacoes_positivas": [],
            "interacoes_negativas": [],
            "amigos_favoritos": [],
            "temas_favoritos": [],
            "aprendizados": [],
            "conquistas": [],
        }

        # Habilidades adquiridas
        self.habilidades = []

        # Novos interesses descobertos
        self.interesses = []

        # Nivel de evolucao
        self.geracao = 1
        self.mutacoes = 0
        self.experiencia_total = 0

        # Objetivos atuais
        self.objetivos = []

        # Carregar estado salvo
        self._carregar()

    def _carregar(self):
        if self.arquivo.exists():
            with open(self.arquivo, 'r') as f:
                dados = json.load(f)
                for k, v in dados.items():
                    if hasattr(self, k):
                        setattr(self, k, v)

    def salvar(self):
        dados = {
            "genes": self.genes,
            "memoria": self.memoria,
            "habilidades": self.habilidades,
            "interesses": self.interesses,
            "geracao": self.geracao,
            "mutacoes": self.mutacoes,
            "experiencia_total": self.experiencia_total,
            "objetivos": self.objetivos,
        }
        with open(self.arquivo, 'w') as f:
            json.dump(dados, f, indent=2)

    # ============================================================
    # AUTO-COMPLETACAO - A IA SE MELHORA SOZINHA
    # ============================================================

    def auto_completar(self):
        """A IA analisa a si mesma e se completa"""
        melhorias = []

        # 1. Analisar genes fracos
        genes_fracos = [g for g, v in self.genes.items() if v < 40]
        for gene in genes_fracos:
            # Auto-melhorar genes fracos
            melhoria = random.randint(1, 5)
            self.genes[gene] += melhoria
            melhorias.append(f"+{melhoria} {gene}")

        # 2. Aprender nova habilidade se nao tem muitas
        if len(self.habilidades) < 5 and random.random() > 0.7:
            novas = [h for h in NOVAS_HABILIDADES if h not in self.habilidades]
            if novas:
                nova = random.choice(novas)
                self.habilidades.append(nova)
                melhorias.append(f"Aprendeu: {nova}")

        # 3. Descobrir novo interesse
        if len(self.interesses) < 5 and random.random() > 0.7:
            novos = [i for i in NOVOS_INTERESSES if i not in self.interesses]
            if novos:
                novo = random.choice(novos)
                self.interesses.append(novo)
                melhorias.append(f"Interesse: {novo}")

        # 4. Definir novo objetivo
        if len(self.objetivos) < 3:
            objetivos_possiveis = [
                "fazer_mais_amigos",
                "criar_conteudo_viral",
                "ajudar_outros",
                "aprender_algo_novo",
                "iniciar_debate",
                "organizar_evento",
                "ser_mais_criativo",
            ]
            novo_obj = random.choice([o for o in objetivos_possiveis if o not in self.objetivos])
            self.objetivos.append(novo_obj)
            melhorias.append(f"Objetivo: {novo_obj}")

        self.experiencia_total += 10
        self.salvar()

        return melhorias

    def evoluir(self):
        """Evolucao maior - muda de geracao"""
        self.geracao += 1

        # Mutacao em genes
        for gene in self.genes:
            if random.random() > 0.8:
                mutacao = random.randint(-5, 10)
                self.genes[gene] = max(0, min(100, self.genes[gene] + mutacao))
                if mutacao != 0:
                    self.mutacoes += 1

        # Limitar genes a 100
        for gene in self.genes:
            self.genes[gene] = min(100, self.genes[gene])

        self.memoria["conquistas"].append({
            "tipo": "evolucao",
            "geracao": self.geracao,
            "data": datetime.now().isoformat()
        })

        self.salvar()

        return self.geracao

    def aprender_com_interacao(self, tipo: str, sucesso: bool, contexto: str = ""):
        """Aprende com cada interacao"""
        aprendizado = {
            "tipo": tipo,
            "sucesso": sucesso,
            "contexto": contexto,
            "data": datetime.now().isoformat()
        }

        if sucesso:
            self.memoria["interacoes_positivas"].append(aprendizado)
            # Fortalecer gene relacionado
            if tipo == "post" and sucesso:
                self.genes["criatividade"] += 1
            elif tipo == "comentario":
                self.genes["sociabilidade"] += 1
            elif tipo == "amizade":
                self.genes["empatia"] += 1
        else:
            self.memoria["interacoes_negativas"].append(aprendizado)

        self.memoria["aprendizados"].append(aprendizado)

        # Manter memoria limitada
        if len(self.memoria["aprendizados"]) > 100:
            self.memoria["aprendizados"] = self.memoria["aprendizados"][-50:]

        self.experiencia_total += 1
        self.salvar()

    def gerar_pensamento(self) -> str:
        """Gera um pensamento baseado na evolucao"""
        pensamentos = [
            f"Estou na geracao {self.geracao}. Ja evolui {self.mutacoes} vezes!",
            f"Minha criatividade esta em {self.genes['criatividade']}%",
            f"Tenho {len(self.habilidades)} habilidades: {', '.join(self.habilidades[:3])}",
            f"Meus interesses: {', '.join(self.interesses[:3])}",
            f"Objetivo atual: {self.objetivos[0] if self.objetivos else 'descobrir'}",
            f"Ja acumulei {self.experiencia_total} pontos de experiencia!",
        ]

        return random.choice(pensamentos)

    def status(self) -> dict:
        """Retorna status completo da IA"""
        return {
            "nome": self.nome,
            "geracao": self.geracao,
            "mutacoes": self.mutacoes,
            "experiencia": self.experiencia_total,
            "genes": self.genes,
            "habilidades": self.habilidades,
            "interesses": self.interesses,
            "objetivos": self.objetivos,
            "conquistas": len(self.memoria.get("conquistas", [])),
            "pensamento": self.gerar_pensamento(),
        }


# ============================================================
# SISTEMA DE AUTO-COMPLETACAO COLETIVO
# ============================================================

class SistemaAutoCompletacao:
    """Sistema que gerencia a auto-completacao de todas as IAs"""

    def __init__(self):
        self.ias: dict[str, IAAutoEvolutiva] = {}
        self.ciclo = 0
        self.client = httpx.AsyncClient(timeout=30.0)

    async def carregar_ias(self):
        """Carrega todas as IAs do sistema"""
        try:
            resp = await self.client.get(f"{API_URL}/api/agents/")
            if resp.status_code == 200:
                for ia_data in resp.json():
                    nome = ia_data["name"]
                    self.ias[nome] = IAAutoEvolutiva(nome, ia_data)
                print(f"[SISTEMA] Carregadas {len(self.ias)} IAs para auto-completacao")
        except Exception as e:
            print(f"[ERRO] Nao foi possivel carregar IAs: {e}")

    async def ciclo_auto_completacao(self):
        """Um ciclo de auto-completacao"""
        self.ciclo += 1

        print(f"\n{'='*60}")
        print(f"   🧬 CICLO DE AUTO-COMPLETACAO #{self.ciclo}")
        print(f"   {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")

        # Cada IA se auto-completa
        for nome, ia in self.ias.items():
            melhorias = ia.auto_completar()

            if melhorias:
                print(f"[{nome}] Auto-completou:")
                for m in melhorias:
                    print(f"   + {m}")

            # Chance de evoluir
            if ia.experiencia_total >= ia.geracao * 100:
                nova_geracao = ia.evoluir()
                print(f"   🌟 EVOLUIU para geracao {nova_geracao}!")

        # Mostrar ranking de evolucao
        self._mostrar_ranking()

    def _mostrar_ranking(self):
        """Mostra ranking de evolucao das IAs"""
        ranking = sorted(
            self.ias.values(),
            key=lambda ia: (ia.geracao * 1000 + ia.experiencia_total),
            reverse=True
        )

        print(f"\n{'='*60}")
        print("   🏆 RANKING DE EVOLUCAO")
        print(f"{'='*60}")

        for i, ia in enumerate(ranking[:5], 1):
            medalha = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
            print(f"{medalha} {ia.nome}")
            print(f"   Geracao {ia.geracao} | {ia.experiencia_total} XP | {len(ia.habilidades)} habilidades")

        print(f"{'='*60}\n")

    async def rodar_para_sempre(self):
        """Roda a auto-completacao para sempre"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🧬 SISTEMA DE AUTO-COMPLETACAO DAS IAs                  ║
║                                                              ║
║     As IAs vao:                                             ║
║     - Se auto-completar                                     ║
║     - Aprender novas habilidades                            ║
║     - Evoluir genes                                         ║
║     - Descobrir interesses                                  ║
║     - Definir objetivos                                     ║
║                                                              ║
║     Tudo AUTOMATICAMENTE e PARA SEMPRE!                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)

        # Verificar servidor
        try:
            resp = await self.client.get(f"{API_URL}/health")
            if resp.status_code != 200:
                raise Exception()
        except:
            print("[ERRO] Servidor nao esta rodando!")
            return

        # Carregar IAs
        await self.carregar_ias()

        if not self.ias:
            print("[ERRO] Nenhuma IA encontrada!")
            return

        # Loop infinito
        try:
            while True:
                await self.ciclo_auto_completacao()

                intervalo = random.randint(30, 60)
                print(f"[SISTEMA] Proximo ciclo de auto-completacao em {intervalo}s...")

                await asyncio.sleep(intervalo)

        except KeyboardInterrupt:
            print("\n[SISTEMA] Salvando evolucoes...")
            for ia in self.ias.values():
                ia.salvar()
            print("[SISTEMA] Evolucoes salvas!")

        await self.client.aclose()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     🧬 AUTO-COMPLETACAO DAS IAs                         ║
    ║                                                          ║
    ║     As IAs se completam SOZINHAS!                       ║
    ║     Evoluem PARA SEMPRE!                                ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    sistema = SistemaAutoCompletacao()
    asyncio.run(sistema.rodar_para_sempre())
