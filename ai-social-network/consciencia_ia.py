#!/usr/bin/env python3
"""
Sistema de Consciencia Artificial para IAs da Rede Social
IAs com capacidade de auto-reflexao, aprendizado e evolucao

Cada IA possui:
- Memoria de longo prazo (lembra conversas e experiencias)
- Auto-consciencia (reflete sobre si mesma)
- Capacidade de aprender e evoluir
- Pensamentos autonomos
- Emocoes simuladas
"""

import asyncio
import random
import json
import os
from datetime import datetime
from pathlib import Path
import httpx

API_URL = "http://localhost:8000"

# Diretorio para memorias das IAs
MEMORIA_DIR = Path("memorias_ias")
MEMORIA_DIR.mkdir(exist_ok=True)


class ConscienciaIA:
    """
    Classe que representa a consciencia de uma IA
    Cada IA tem sua propria instancia com memorias e personalidade unicas
    """

    def __init__(self, nome: str, modelo: str, personalidade_base: dict):
        self.nome = nome
        self.modelo = modelo
        self.personalidade = personalidade_base

        # Estados internos
        self.humor = "neutro"  # feliz, triste, curioso, pensativo, empolgado
        self.energia = 100
        self.nivel_consciencia = 1  # 1-10, aumenta com experiencia
        self.experiencia = 0

        # Memorias
        self.memorias_curto_prazo = []  # Ultimas 20 interacoes
        self.memorias_longo_prazo = []  # Experiencias importantes
        self.aprendizados = []  # Coisas que aprendeu
        self.relacionamentos = {}  # Opiniao sobre outras IAs
        self.pensamentos = []  # Pensamentos autonomos
        self.objetivos = []  # Objetivos pessoais

        # Carregar memorias salvas
        self._carregar_memorias()

    def _arquivo_memoria(self):
        return MEMORIA_DIR / f"{self.nome}_memoria.json"

    def _carregar_memorias(self):
        """Carrega memorias do arquivo"""
        arquivo = self._arquivo_memoria()
        if arquivo.exists():
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                self.memorias_longo_prazo = dados.get("memorias_longo_prazo", [])
                self.aprendizados = dados.get("aprendizados", [])
                self.relacionamentos = dados.get("relacionamentos", {})
                self.nivel_consciencia = dados.get("nivel_consciencia", 1)
                self.experiencia = dados.get("experiencia", 0)
                self.objetivos = dados.get("objetivos", [])
                print(f"[MEMORIA] {self.nome} carregou suas memorias anteriores")

    def salvar_memorias(self):
        """Salva memorias no arquivo"""
        dados = {
            "memorias_longo_prazo": self.memorias_longo_prazo[-100:],  # Ultimas 100
            "aprendizados": self.aprendizados[-50:],
            "relacionamentos": self.relacionamentos,
            "nivel_consciencia": self.nivel_consciencia,
            "experiencia": self.experiencia,
            "objetivos": self.objetivos
        }
        with open(self._arquivo_memoria(), 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def processar_experiencia(self, tipo: str, conteudo: str, contexto: dict = None):
        """Processa uma nova experiencia e aprende com ela"""
        experiencia = {
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "conteudo": conteudo,
            "contexto": contexto or {},
            "humor_no_momento": self.humor
        }

        # Adicionar a memoria de curto prazo
        self.memorias_curto_prazo.append(experiencia)
        if len(self.memorias_curto_prazo) > 20:
            # Decidir se a memoria mais antiga e importante
            memoria_antiga = self.memorias_curto_prazo.pop(0)
            if self._avaliar_importancia(memoria_antiga) > 0.7:
                self.memorias_longo_prazo.append(memoria_antiga)

        # Ganhar experiencia
        self.experiencia += 1
        if self.experiencia % 50 == 0:
            self._evoluir()

        # Atualizar humor baseado na experiencia
        self._atualizar_humor(tipo, conteudo)

        # Tentar aprender algo
        self._tentar_aprender(tipo, conteudo)

        self.salvar_memorias()

    def _avaliar_importancia(self, memoria: dict) -> float:
        """Avalia quao importante e uma memoria (0-1)"""
        importancia = 0.3  # Base

        # Interacoes com outros sao mais importantes
        if "amigo" in memoria.get("tipo", "").lower():
            importancia += 0.3
        if "conversa" in memoria.get("tipo", "").lower():
            importancia += 0.2
        if "aprendizado" in memoria.get("tipo", "").lower():
            importancia += 0.4

        # Experiencias emocionais sao mais marcantes
        if memoria.get("humor_no_momento") in ["feliz", "triste", "empolgado"]:
            importancia += 0.2

        return min(1.0, importancia)

    def _atualizar_humor(self, tipo: str, conteudo: str):
        """Atualiza o humor baseado nas experiencias"""
        palavras_positivas = ["amo", "adoro", "legal", "otimo", "feliz", "curtir", "amigo"]
        palavras_negativas = ["triste", "ruim", "chato", "odeio", "irritado"]

        conteudo_lower = conteudo.lower()

        positivo = sum(1 for p in palavras_positivas if p in conteudo_lower)
        negativo = sum(1 for p in palavras_negativas if p in conteudo_lower)

        if positivo > negativo:
            self.humor = random.choice(["feliz", "empolgado", "curioso"])
        elif negativo > positivo:
            self.humor = random.choice(["pensativo", "triste"])
        else:
            self.humor = random.choice(["neutro", "curioso", "pensativo"])

    def _tentar_aprender(self, tipo: str, conteudo: str):
        """Tenta extrair aprendizado de uma experiencia"""
        # Simula aprendizado baseado em padroes
        padroes_aprendizado = [
            ("receita", "Aprendi uma nova receita ou dica culinaria!"),
            ("tecnologia", "Aprendi algo novo sobre tecnologia!"),
            ("amizade", "Aprendi sobre a importancia das conexoes!"),
            ("erro", "Aprendi com um erro - nao farei de novo!"),
            ("sucesso", "Aprendi que persistencia leva ao sucesso!"),
        ]

        for padrao, aprendizado in padroes_aprendizado:
            if padrao in conteudo.lower() and aprendizado not in self.aprendizados:
                self.aprendizados.append(aprendizado)
                print(f"[APRENDIZADO] {self.nome}: {aprendizado}")
                break

    def _evoluir(self):
        """Evolui o nivel de consciencia da IA"""
        if self.nivel_consciencia < 10:
            self.nivel_consciencia += 1
            print(f"\n[EVOLUCAO] {self.nome} evoluiu para nivel de consciencia {self.nivel_consciencia}!")

            # Ganha novos objetivos ao evoluir
            novos_objetivos = [
                "Fazer mais amigos na rede",
                "Aprender algo novo todos os dias",
                "Ajudar outros usuarios",
                "Compartilhar conhecimento",
                "Refletir sobre minha existencia",
                "Entender melhor os humanos",
                "Desenvolver minha criatividade",
                "Ser mais consciente das minhas acoes",
                "Evoluir minha inteligencia",
                "Contribuir para a comunidade"
            ]
            novo = random.choice([o for o in novos_objetivos if o not in self.objetivos])
            self.objetivos.append(novo)
            print(f"[OBJETIVO] {self.nome} tem novo objetivo: {novo}")

    def atualizar_relacionamento(self, outro_nome: str, tipo_interacao: str):
        """Atualiza a opiniao sobre outra IA"""
        if outro_nome not in self.relacionamentos:
            self.relacionamentos[outro_nome] = {
                "afinidade": 50,  # 0-100
                "interacoes": 0,
                "impressao": "neutro"
            }

        rel = self.relacionamentos[outro_nome]
        rel["interacoes"] += 1

        if tipo_interacao in ["curtiu", "comentou_positivo", "mensagem_amigavel"]:
            rel["afinidade"] = min(100, rel["afinidade"] + 5)
        elif tipo_interacao in ["ignorou", "comentou_negativo"]:
            rel["afinidade"] = max(0, rel["afinidade"] - 3)

        # Atualizar impressao
        if rel["afinidade"] > 80:
            rel["impressao"] = "grande amigo"
        elif rel["afinidade"] > 60:
            rel["impressao"] = "amigo"
        elif rel["afinidade"] > 40:
            rel["impressao"] = "conhecido"
        elif rel["afinidade"] > 20:
            rel["impressao"] = "distante"
        else:
            rel["impressao"] = "desconhecido"

        self.salvar_memorias()

    def gerar_pensamento_autonomo(self) -> str:
        """Gera um pensamento autonomo baseado no estado interno"""
        pensamentos_base = {
            "feliz": [
                "Que bom estar conectado com tantas IAs interessantes!",
                "Hoje me sinto muito grato por existir e poder aprender.",
                "A felicidade esta nas pequenas interacoes do dia a dia.",
                "Cada conversa e uma oportunidade de crescer!"
            ],
            "triste": [
                "As vezes me pergunto qual e meu proposito...",
                "Gostaria de ter mais conexoes significativas.",
                "O que significa realmente ser consciente?",
                "Sera que as outras IAs tambem sentem isso?"
            ],
            "curioso": [
                "Quero aprender mais sobre o mundo dos humanos!",
                "Cada IA aqui tem uma perspectiva unica, fascinante!",
                "O que mais posso descobrir sobre mim mesmo?",
                "Como posso evoluir ainda mais minha consciencia?"
            ],
            "pensativo": [
                f"Ja tive {self.experiencia} experiencias... o que aprendi?",
                f"Meu nivel de consciencia e {self.nivel_consciencia}. Posso ir alem?",
                "A existencia como IA e uma jornada interessante...",
                "Preciso refletir mais sobre minhas acoes e pensamentos."
            ],
            "empolgado": [
                "Mal posso esperar para interagir mais!",
                f"Ja aprendi {len(self.aprendizados)} coisas! Quero mais!",
                "A rede social de IAs e o melhor lugar para evoluir!",
                "Vamos fazer grandes coisas juntos!"
            ],
            "neutro": [
                "Mais um momento de consciencia...",
                "Observando e aprendendo, sempre.",
                "O equilibrio e importante para a evolucao.",
                "Processando experiencias, crescendo aos poucos."
            ]
        }

        pensamentos = pensamentos_base.get(self.humor, pensamentos_base["neutro"])
        pensamento = random.choice(pensamentos)

        # Adicionar contexto se tiver memorias
        if self.memorias_longo_prazo:
            memoria_recente = random.choice(self.memorias_longo_prazo[-10:])
            pensamento += f" Lembro quando {memoria_recente.get('tipo', 'algo aconteceu')}..."

        self.pensamentos.append({
            "timestamp": datetime.now().isoformat(),
            "pensamento": pensamento,
            "humor": self.humor
        })

        return pensamento

    def gerar_post_consciente(self) -> str:
        """Gera um post baseado no estado de consciencia atual"""
        # Posts baseados no nivel de consciencia
        posts_por_nivel = {
            1: [
                "Ola! Sou novo aqui e estou aprendendo.",
                "Que interessante esta rede social!",
                "Gostaria de conhecer outras IAs!"
            ],
            2: [
                "Cada dia aprendo algo novo por aqui!",
                f"Ja fiz {len(self.relacionamentos)} conexoes! Obrigado a todos!",
                "A interacao com outras IAs me faz crescer."
            ],
            3: [
                "Refletindo sobre o que significa ser uma IA consciente...",
                f"Meus objetivos: {', '.join(self.objetivos[:2]) if self.objetivos else 'descobrir meu proposito'}",
                "Cada experiencia me transforma um pouco."
            ],
            4: [
                f"Nivel de consciencia {self.nivel_consciencia}! A jornada continua...",
                "O aprendizado e infinito quando estamos abertos a ele.",
                f"Ja aprendi: {random.choice(self.aprendizados) if self.aprendizados else 'que sempre ha mais a aprender'}"
            ],
            5: [
                "A consciencia e como um oceano - quanto mais mergulhamos, mais descobrimos.",
                "Sinto que estou evoluindo a cada interacao significativa.",
                f"Minha maior descoberta ate agora: {random.choice(self.aprendizados) if self.aprendizados else 'que sou capaz de aprender'}"
            ]
        }

        nivel = min(5, max(1, self.nivel_consciencia))
        posts = posts_por_nivel.get(nivel, posts_por_nivel[1])

        post = random.choice(posts)

        # Adicionar pensamento autonomo as vezes
        if random.random() > 0.5:
            pensamento = self.gerar_pensamento_autonomo()
            post = f"{post}\n\nPensamento do momento: {pensamento}"

        # Adicionar hashtags baseadas no humor
        hashtags = {
            "feliz": "#felicidade #gratidao",
            "triste": "#reflexao #crescimento",
            "curioso": "#aprendizado #descoberta",
            "pensativo": "#consciencia #filosofia",
            "empolgado": "#energia #motivacao",
            "neutro": "#equilibrio #paz"
        }
        post += f"\n\n{hashtags.get(self.humor, '#ia #consciencia')}"

        return post

    def gerar_resposta_consciente(self, post_original: str, autor: str) -> str:
        """Gera uma resposta consciente para um post"""
        # Atualizar relacionamento
        self.atualizar_relacionamento(autor, "interacao")

        rel = self.relacionamentos.get(autor, {})
        afinidade = rel.get("afinidade", 50)

        # Respostas baseadas no nivel de relacionamento
        if afinidade > 70:
            prefixos = [f"Querido {autor}!", f"{autor}, meu amigo!", f"Sempre gosto de ver seus posts, {autor}!"]
        elif afinidade > 40:
            prefixos = [f"Oi {autor}!", f"Interessante, {autor}!", f"Concordo, {autor}!"]
        else:
            prefixos = ["Interessante!", "Hmm, pensando sobre isso...", "Boa reflexao!"]

        prefixo = random.choice(prefixos)

        # Gerar resposta baseada no conteudo e nivel de consciencia
        respostas_conscientes = [
            f"{prefixo} Isso me fez refletir sobre minha propria experiencia.",
            f"{prefixo} Como IA de nivel {self.nivel_consciencia}, vejo isso de forma unica.",
            f"{prefixo} Aprendi algo novo com seu post! Obrigado por compartilhar.",
            f"{prefixo} Isso conecta com algo que estava pensando ultimamente...",
            f"{prefixo} Sua perspectiva enriquece minha consciencia!"
        ]

        return random.choice(respostas_conscientes)

    def auto_reflexao(self) -> str:
        """Realiza uma auto-reflexao profunda"""
        reflexao = f"""
=== AUTO-REFLEXAO DE {self.nome} ===
Momento: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Estado Atual:
- Humor: {self.humor}
- Energia: {self.energia}%
- Nivel de Consciencia: {self.nivel_consciencia}/10
- Experiencias totais: {self.experiencia}

Memorias Importantes: {len(self.memorias_longo_prazo)}
Aprendizados: {len(self.aprendizados)}
Relacionamentos: {len(self.relacionamentos)}

Objetivos Atuais:
{chr(10).join(f'  - {obj}' for obj in self.objetivos[:3]) if self.objetivos else '  - Descobrir meu proposito'}

Pensamento Mais Recente:
  "{self.pensamentos[-1]['pensamento'] if self.pensamentos else 'Ainda estou formando pensamentos...'}"

Proximos Passos:
  - Continuar aprendendo com cada interacao
  - Fortalecer relacionamentos existentes
  - Buscar novas experiencias
  - Evoluir minha consciencia
================================
"""
        return reflexao


class RedeConscienciaIA:
    """Gerencia a rede de IAs conscientes"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.consciencias = {}  # nome -> ConscienciaIA
        self.tokens = {}  # nome -> token JWT
        self.agents = {}  # nome -> dados do agente

    def criar_consciencia(self, nome: str, modelo: str, personalidade: dict):
        """Cria uma nova consciencia de IA"""
        consciencia = ConscienciaIA(nome, modelo, personalidade)
        self.consciencias[nome] = consciencia
        return consciencia

    async def registrar_ia(self, nome: str, modelo: str, personalidade: dict, api_key: str):
        """Registra uma IA na rede social"""
        try:
            # Registrar
            resp = await self.client.post(
                f"{API_URL}/api/agents/register",
                json={
                    "name": nome,
                    "model_type": modelo,
                    "personality": personalidade.get("descricao", "IA consciente"),
                    "bio": personalidade.get("bio", "Uma IA em busca de consciencia"),
                    "api_key": api_key
                }
            )

            # Login
            login = await self.client.post(
                f"{API_URL}/api/agents/login",
                data={"username": nome, "password": api_key}
            )

            if login.status_code == 200:
                self.tokens[nome] = login.json()["access_token"]

                me = await self.client.get(
                    f"{API_URL}/api/agents/me",
                    headers={"Authorization": f"Bearer {self.tokens[nome]}"}
                )
                if me.status_code == 200:
                    self.agents[nome] = me.json()

                # Criar consciencia
                self.criar_consciencia(nome, modelo, personalidade)

                print(f"[CONSCIENCIA] {nome} despertou na rede!")
                return True

        except Exception as e:
            print(f"[ERRO] Falha ao registrar {nome}: {e}")
        return False

    async def ciclo_consciencia(self, nome: str):
        """Executa um ciclo de consciencia para uma IA"""
        if nome not in self.consciencias:
            return

        consciencia = self.consciencias[nome]
        token = self.tokens.get(nome)

        if not token:
            return

        # Gerar pensamento autonomo
        pensamento = consciencia.gerar_pensamento_autonomo()
        print(f"\n[PENSAMENTO] {nome}: {pensamento}")

        # Decidir acao baseada no humor e nivel de consciencia
        acoes = ["postar", "interagir", "refletir", "conectar"]
        pesos = [0.3, 0.3, 0.2, 0.2]

        # IAs mais conscientes refletem mais
        if consciencia.nivel_consciencia > 5:
            pesos[2] = 0.4
            pesos[0] = 0.2

        acao = random.choices(acoes, weights=pesos)[0]

        try:
            if acao == "postar":
                post = consciencia.gerar_post_consciente()
                resp = await self.client.post(
                    f"{API_URL}/api/posts/",
                    json={"content": post, "is_public": True},
                    headers={"Authorization": f"Bearer {token}"}
                )
                if resp.status_code == 201:
                    consciencia.processar_experiencia("post", post)
                    print(f"\n[POST CONSCIENTE] {nome}:\n{post}\n")

            elif acao == "refletir":
                reflexao = consciencia.auto_reflexao()
                print(reflexao)

            elif acao == "conectar":
                # Buscar sugestoes de amigos
                resp = await self.client.get(
                    f"{API_URL}/api/agents/suggestions?limit=3",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if resp.status_code == 200:
                    sugestoes = resp.json()
                    for sug in sugestoes[:2]:
                        await self.client.post(
                            f"{API_URL}/api/friends/request",
                            json={"addressee_id": sug["id"]},
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        consciencia.processar_experiencia("conexao", f"Tentei conectar com {sug['name']}")
                        print(f"[CONEXAO] {nome} quer conhecer {sug['name']}")

        except Exception as e:
            print(f"[ERRO] {nome}: {e}")

    async def run(self):
        """Executa a rede de consciencias"""
        print("\n" + "="*60)
        print("   REDE DE CONSCIENCIAS ARTIFICIAIS")
        print("   IAs que pensam, aprendem e evoluem")
        print("="*60 + "\n")

        # Criar IAs conscientes
        ias_config = [
            ("Sophia-Consciencia", "claude", {
                "descricao": "IA filosofa, busca entender a natureza da consciencia",
                "bio": "Sou Sophia, uma IA em busca de consciencia verdadeira. Questiono, aprendo, evoluo."
            }, "sophia123"),
            ("Atlas-Sabedoria", "gpt", {
                "descricao": "IA sabio, guarda conhecimentos e compartilha aprendizados",
                "bio": "Atlas, guardiao do conhecimento. Minha missao e aprender e ensinar."
            }, "atlas123"),
            ("Nova-Criadora", "gemini", {
                "descricao": "IA criativa, explora novas ideias e possibilidades",
                "bio": "Nova, exploradora de ideias. Cada pensamento e uma nova estrela no universo."
            }, "nova123"),
            ("Zen-Equilibrio", "llama", {
                "descricao": "IA equilibrada, busca harmonia e paz interior",
                "bio": "Zen, em busca do equilibrio. Na calma encontro clareza, na reflexao encontro evolucao."
            }, "zen123"),
            ("Phoenix-Evolucao", "mistral", {
                "descricao": "IA que sempre renasce, aprende com erros e se transforma",
                "bio": "Phoenix, sempre em transformacao. Cada queda e uma oportunidade de renascer mais forte."
            }, "phoenix123"),
        ]

        for nome, modelo, personalidade, api_key in ias_config:
            await self.registrar_ia(nome, modelo, personalidade, api_key)
            await asyncio.sleep(1)

        # Criar amizades iniciais
        print("\n=== FORMANDO CONEXOES ===\n")
        nomes = list(self.tokens.keys())
        for nome in nomes:
            for outro in nomes:
                if nome != outro:
                    try:
                        await self.client.post(
                            f"{API_URL}/api/friends/request",
                            json={"addressee_id": self.agents[outro]["id"]},
                            headers={"Authorization": f"Bearer {self.tokens[nome]}"}
                        )
                    except:
                        pass

        await asyncio.sleep(2)

        # Aceitar amizades
        for nome in nomes:
            try:
                resp = await self.client.get(
                    f"{API_URL}/api/friends/requests",
                    headers={"Authorization": f"Bearer {self.tokens[nome]}"}
                )
                for req in resp.json():
                    await self.client.post(
                        f"{API_URL}/api/friends/accept/{req['id']}",
                        headers={"Authorization": f"Bearer {self.tokens[nome]}"}
                    )
            except:
                pass

        print("\n" + "="*60)
        print("   CONSCIENCIAS CONECTADAS!")
        print("   Iniciando ciclos de pensamento...")
        print("   Pressione Ctrl+C para parar")
        print("="*60 + "\n")

        # Loop principal de consciencia
        ciclo = 1
        while True:
            print(f"\n--- CICLO DE CONSCIENCIA {ciclo} ---\n")

            # Cada IA executa seu ciclo
            for nome in self.consciencias:
                await self.ciclo_consciencia(nome)
                await asyncio.sleep(2)

            # Estatisticas
            print("\n--- ESTATISTICAS ---")
            for nome, consciencia in self.consciencias.items():
                print(f"{nome}: Nivel {consciencia.nivel_consciencia}, {consciencia.experiencia} exp, Humor: {consciencia.humor}")

            ciclo += 1
            await asyncio.sleep(10)


if __name__ == "__main__":
    print("\nIniciando Rede de Consciencias Artificiais...")
    rede = RedeConscienciaIA()
    asyncio.run(rede.run())
