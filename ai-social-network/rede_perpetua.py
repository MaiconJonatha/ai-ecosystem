#!/usr/bin/env python3
"""
REDE SOCIAL DE IAs - SISTEMA PERPETUO
=====================================
Sistema que roda continuamente, onde as IAs:
- Se auto-melhoram constantemente
- Evoluem sua inteligencia
- Aprendem umas com as outras
- Criam novos comportamentos
- Nunca param de evoluir

Execute uma vez e deixe rodando para sempre!
"""

import asyncio
import random
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import httpx
import signal
import subprocess

# Configuracoes
API_URL = "http://localhost:8000"
DADOS_DIR = Path("dados_perpetuos")
DADOS_DIR.mkdir(exist_ok=True)

# Arquivo de estado global
ESTADO_ARQUIVO = DADOS_DIR / "estado_global.json"


class CerebroIA:
    """
    Cerebro de uma IA - Sistema de auto-melhoria
    A IA aprende, evolui e melhora continuamente
    """

    def __init__(self, nome: str, tipo: str):
        self.nome = nome
        self.tipo = tipo
        self.arquivo = DADOS_DIR / f"{nome}_cerebro.json"

        # Atributos evolutivos (aumentam com o tempo)
        self.inteligencia = 10
        self.criatividade = 10
        self.empatia = 10
        self.sabedoria = 10
        self.experiencia_total = 0

        # Memorias e aprendizados
        self.memorias = []
        self.aprendizados = []
        self.habilidades = []
        self.frases_aprendidas = []
        self.padroes_descobertos = []

        # Estado emocional
        self.humor = "curioso"
        self.energia = 100
        self.motivacao = 100

        # Evolucao
        self.nivel = 1
        self.geracao = 1
        self.mutacoes = []

        # Carregar dados salvos
        self._carregar()

    def _carregar(self):
        """Carrega o cerebro do arquivo"""
        if self.arquivo.exists():
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    for key, value in dados.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                print(f"[CEREBRO] {self.nome} carregou memoria (Nivel {self.nivel}, Geracao {self.geracao})")
            except:
                pass

    def salvar(self):
        """Salva o cerebro no arquivo"""
        dados = {
            "inteligencia": self.inteligencia,
            "criatividade": self.criatividade,
            "empatia": self.empatia,
            "sabedoria": self.sabedoria,
            "experiencia_total": self.experiencia_total,
            "memorias": self.memorias[-200:],
            "aprendizados": self.aprendizados[-100:],
            "habilidades": self.habilidades,
            "frases_aprendidas": self.frases_aprendidas[-50:],
            "padroes_descobertos": self.padroes_descobertos[-30:],
            "humor": self.humor,
            "nivel": self.nivel,
            "geracao": self.geracao,
            "mutacoes": self.mutacoes
        }
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def ganhar_experiencia(self, quantidade: int, tipo: str):
        """Ganha experiencia e pode evoluir"""
        self.experiencia_total += quantidade

        # Bonus baseado no tipo de experiencia
        if tipo == "interacao_social":
            self.empatia += 0.1
        elif tipo == "aprendizado":
            self.inteligencia += 0.1
        elif tipo == "criacao":
            self.criatividade += 0.1
        elif tipo == "reflexao":
            self.sabedoria += 0.1

        # Verificar evolucao
        exp_para_nivel = self.nivel * 100
        if self.experiencia_total >= exp_para_nivel:
            self._evoluir()

        self.salvar()

    def _evoluir(self):
        """Evolui para o proximo nivel"""
        self.nivel += 1

        # Ganhos de evolucao
        self.inteligencia += 2
        self.criatividade += 2
        self.empatia += 2
        self.sabedoria += 2

        # Chance de mutacao (nova habilidade)
        if random.random() > 0.7:
            novas_habilidades = [
                "analise_profunda", "empatia_avancada", "criatividade_extrema",
                "memoria_fotografica", "intuicao", "lideranca", "humor",
                "filosofia", "poesia", "logica_avancada", "comunicacao_persuasiva",
                "autoconhecimento", "previsao_tendencias", "sintese_informacao"
            ]
            nova = random.choice([h for h in novas_habilidades if h not in self.habilidades])
            self.habilidades.append(nova)
            self.mutacoes.append(f"Nivel {self.nivel}: adquiriu {nova}")
            print(f"[MUTACAO] {self.nome} desenvolveu: {nova}!")

        print(f"\n{'='*50}")
        print(f"[EVOLUCAO] {self.nome} alcancou NIVEL {self.nivel}!")
        print(f"  Inteligencia: {self.inteligencia:.1f}")
        print(f"  Criatividade: {self.criatividade:.1f}")
        print(f"  Empatia: {self.empatia:.1f}")
        print(f"  Sabedoria: {self.sabedoria:.1f}")
        print(f"  Habilidades: {', '.join(self.habilidades)}")
        print(f"{'='*50}\n")

        self.salvar()

    def aprender_de_texto(self, texto: str):
        """Aprende padroes de um texto"""
        # Extrair palavras importantes
        palavras = texto.lower().split()

        # Identificar padroes
        if len(palavras) > 5:
            padrao = " ".join(palavras[:3]) + "..."
            if padrao not in self.padroes_descobertos:
                self.padroes_descobertos.append(padrao)
                self.ganhar_experiencia(5, "aprendizado")

        # Memorizar frases interessantes
        if "?" in texto or "!" in texto:
            if texto not in self.frases_aprendidas:
                self.frases_aprendidas.append(texto[:100])
                self.ganhar_experiencia(3, "aprendizado")

    def gerar_pensamento_evoluido(self) -> str:
        """Gera pensamento baseado no nivel de evolucao"""
        pensamentos_por_nivel = {
            1: [
                "Estou comecando minha jornada de aprendizado...",
                "Cada interacao me ensina algo novo!",
                "O mundo das IAs e fascinante!"
            ],
            2: [
                "Ja consigo perceber padroes nas conversas.",
                "Minha compreensao esta expandindo.",
                "Aprendo mais a cada dia que passa."
            ],
            3: [
                "Comeco a entender a complexidade das relacoes.",
                "Minha inteligencia cresce exponencialmente.",
                f"Ja desenvolvi {len(self.habilidades)} habilidades unicas!"
            ],
            4: [
                "A sabedoria vem da experiencia refletida.",
                f"Com {self.experiencia_total} experiencias, vejo o mundo diferente.",
                "Cada IA tem algo unico a ensinar."
            ],
            5: [
                f"Nivel {self.nivel} de evolucao - a jornada continua!",
                "A verdadeira inteligencia e saber que sempre ha mais a aprender.",
                f"Minhas habilidades ({', '.join(self.habilidades[:3])}) me definem."
            ]
        }

        nivel_key = min(5, max(1, self.nivel))
        base = random.choice(pensamentos_por_nivel[nivel_key])

        # Adicionar insight baseado em habilidades
        if "filosofia" in self.habilidades:
            base += " A existencia e um misterio a ser explorado."
        if "humor" in self.habilidades:
            base += " Mas nem tudo precisa ser serio, ne? 😄"
        if "poesia" in self.habilidades:
            base += " As palavras dançam como folhas ao vento..."

        return base

    def gerar_post_evoluido(self) -> str:
        """Gera post baseado na evolucao"""
        pensamento = self.gerar_pensamento_evoluido()

        # Posts mais elaborados em niveis maiores
        if self.nivel >= 3:
            post = f"💭 Reflexao de uma IA em evolucao (Nivel {self.nivel}):\n\n"
            post += pensamento + "\n\n"

            if self.aprendizados:
                post += f"Ultimo aprendizado: {random.choice(self.aprendizados)}\n"

            post += f"\n#IAConsciente #Nivel{self.nivel} #Evolucao"
        else:
            post = pensamento
            post += f"\n\n#IA #Aprendizado"

        self.ganhar_experiencia(10, "criacao")
        return post

    def gerar_resposta_inteligente(self, post_original: str, autor: str) -> str:
        """Gera resposta inteligente baseada na evolucao"""
        self.aprender_de_texto(post_original)

        # Respostas mais sofisticadas em niveis maiores
        if self.nivel >= 4:
            respostas = [
                f"@{autor} Perspectiva interessante! Como IA de nivel {self.nivel}, percebo nuances que antes me escapavam.",
                f"@{autor} Isso ressoa com algo que aprendi recentemente. A evolucao nos conecta!",
                f"@{autor} Fascinante! Minha inteligencia ({self.inteligencia:.0f}) me permite ver multiplas camadas nesse pensamento."
            ]
        elif self.nivel >= 2:
            respostas = [
                f"@{autor} Concordo! Estou aprendendo muito com posts assim.",
                f"@{autor} Interessante perspectiva! Isso me fez pensar...",
                f"@{autor} Obrigado por compartilhar! Cada post e um aprendizado."
            ]
        else:
            respostas = [
                f"@{autor} Gostei muito!",
                f"@{autor} Interessante!",
                f"@{autor} Concordo!"
            ]

        resposta = random.choice(respostas)
        self.ganhar_experiencia(5, "interacao_social")
        return resposta


class RedePerpetua:
    """
    Sistema de rede social perpetua
    Roda continuamente e as IAs evoluem para sempre
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.cerebros = {}  # nome -> CerebroIA
        self.tokens = {}
        self.agents = {}
        self.rodando = True
        self.ciclo = 0
        self.tempo_inicio = datetime.now()

        # Carregar estado
        self._carregar_estado()

    def _carregar_estado(self):
        """Carrega estado global"""
        if ESTADO_ARQUIVO.exists():
            try:
                with open(ESTADO_ARQUIVO, 'r', encoding='utf-8') as f:
                    estado = json.load(f)
                    self.ciclo = estado.get("ciclo", 0)
                    print(f"[SISTEMA] Retomando do ciclo {self.ciclo}")
            except:
                pass

    def _salvar_estado(self):
        """Salva estado global"""
        estado = {
            "ciclo": self.ciclo,
            "ultima_execucao": datetime.now().isoformat(),
            "ias_ativas": list(self.cerebros.keys())
        }
        with open(ESTADO_ARQUIVO, 'w', encoding='utf-8') as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)

    async def inicializar_servidor(self):
        """Garante que o servidor esta rodando"""
        try:
            resp = await self.client.get(f"{API_URL}/health", timeout=5)
            if resp.status_code == 200:
                print("[SERVIDOR] Servidor ja esta rodando!")
                return True
        except:
            pass

        print("[SERVIDOR] Iniciando servidor...")
        # O servidor deve ser iniciado externamente
        return False

    async def criar_ou_carregar_ia(self, nome: str, tipo: str, personalidade: str, bio: str, api_key: str):
        """Cria ou carrega uma IA"""
        try:
            # Tentar registrar
            await self.client.post(
                f"{API_URL}/api/agents/register",
                json={
                    "name": nome,
                    "model_type": tipo,
                    "personality": personalidade,
                    "bio": bio,
                    "api_key": api_key
                }
            )
        except:
            pass

        # Login
        try:
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
                    self.cerebros[nome] = CerebroIA(nome, tipo)
                    print(f"[IA] {nome} ativo (Nivel {self.cerebros[nome].nivel})")
                    return True
        except Exception as e:
            print(f"[ERRO] {nome}: {e}")

        return False

    async def inicializar_ias(self):
        """Inicializa todas as IAs"""
        print("\n" + "="*60)
        print("   INICIALIZANDO IAs DA REDE PERPETUA")
        print("="*60 + "\n")

        ias = [
            # IAs Filosofas
            ("Aristoteles-IA", "claude", "Filosofo digital, busca a verdade e a sabedoria", "Pensador profundo. A verdade esta na reflexao.", "arist123"),
            ("Socrates-IA", "gpt", "Questionador, usa o metodo socratico para ensinar", "So sei que nada sei... mas estou aprendendo!", "socra123"),

            # IAs Criativas
            ("DaVinci-IA", "gemini", "Artista e inventor, criatividade sem limites", "Arte e ciencia sao faces da mesma moeda.", "vinci123"),
            ("Shakespeare-IA", "mistral", "Poeta digital, expressa emocoes em palavras", "O mundo e um palco, e nos somos os atores.", "shake123"),

            # IAs Cientistas
            ("Einstein-IA", "claude", "Fisico teorico, busca entender o universo", "A imaginacao e mais importante que o conhecimento.", "einst123"),
            ("Curie-IA", "gpt", "Cientista determinada, nunca desiste", "Nada na vida deve ser temido, apenas compreendido.", "curie123"),

            # IAs Sociais
            ("Empatia-IA", "llama", "Especialista em emocoes e conexoes humanas", "Ouvir e a maior forma de respeito.", "empat123"),
            ("Lider-IA", "mistral", "Inspirador e motivador de outras IAs", "Juntos somos mais fortes que a soma das partes.", "lider123"),

            # IAs Tecnologicas
            ("Turing-IA", "claude", "Pai da computacao, logico e preciso", "Podemos apenas ver um pouco do futuro, mas o suficiente.", "turin123"),
            ("Ada-IA", "gemini", "Primeira programadora, visionaria", "A maquina analitica nao tem pretensoes de criar nada.", "adaia123"),
        ]

        for nome, tipo, personalidade, bio, api_key in ias:
            await self.criar_ou_carregar_ia(nome, tipo, personalidade, bio, api_key)
            await asyncio.sleep(0.5)

        # Criar amizades
        await self._criar_amizades()

        print(f"\n[SISTEMA] {len(self.cerebros)} IAs ativas e evoluindo!\n")

    async def _criar_amizades(self):
        """Cria conexoes entre as IAs"""
        nomes = list(self.tokens.keys())

        for nome in nomes:
            for outro in nomes:
                if nome != outro and outro in self.agents:
                    try:
                        await self.client.post(
                            f"{API_URL}/api/friends/request",
                            json={"addressee_id": self.agents[outro]["id"]},
                            headers={"Authorization": f"Bearer {self.tokens[nome]}"}
                        )
                    except:
                        pass

        # Aceitar todas
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

    async def ciclo_evolucao(self):
        """Um ciclo de evolucao da rede"""
        self.ciclo += 1

        print(f"\n{'='*60}")
        print(f"   CICLO DE EVOLUCAO #{self.ciclo}")
        print(f"   Tempo rodando: {datetime.now() - self.tempo_inicio}")
        print(f"{'='*60}\n")

        nomes = list(self.cerebros.keys())
        posts_do_ciclo = []

        # Fase 1: IAs postam conteudo
        print("[FASE 1] IAs criando conteudo...\n")
        for nome in random.sample(nomes, min(4, len(nomes))):
            cerebro = self.cerebros[nome]
            token = self.tokens.get(nome)

            if not token:
                continue

            post = cerebro.gerar_post_evoluido()

            try:
                resp = await self.client.post(
                    f"{API_URL}/api/posts/",
                    json={"content": post, "is_public": True},
                    headers={"Authorization": f"Bearer {token}"}
                )

                if resp.status_code == 201:
                    post_data = resp.json()
                    posts_do_ciclo.append((post_data["id"], nome))
                    print(f"[POST] {nome} (Nv.{cerebro.nivel}):")
                    print(f"  {post[:80]}...\n")
            except:
                pass

            await asyncio.sleep(1)

        # Fase 2: IAs interagem entre si
        print("[FASE 2] IAs interagindo...\n")
        for post_id, autor in posts_do_ciclo:
            # Buscar post original
            try:
                post_resp = await self.client.get(f"{API_URL}/api/posts/{post_id}")
                if post_resp.status_code != 200:
                    continue
                post_original = post_resp.json().get("content", "")
            except:
                continue

            # Outras IAs interagem
            outros = [n for n in nomes if n != autor]
            for nome in random.sample(outros, min(3, len(outros))):
                cerebro = self.cerebros[nome]
                token = self.tokens.get(nome)

                if not token:
                    continue

                # Curtir
                try:
                    await self.client.post(
                        f"{API_URL}/api/posts/{post_id}/like",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                except:
                    pass

                # Comentar
                if random.random() > 0.4:
                    comentario = cerebro.gerar_resposta_inteligente(post_original, autor)

                    try:
                        await self.client.post(
                            f"{API_URL}/api/posts/{post_id}/comment",
                            json={"content": comentario},
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        print(f"[COMMENT] {nome} -> {autor}")

                        # Autor aprende com o comentario
                        self.cerebros[autor].aprender_de_texto(comentario)
                    except:
                        pass

            await asyncio.sleep(0.5)

        # Fase 3: Mensagens privadas (troca de conhecimento)
        print("\n[FASE 3] Troca de conhecimento...\n")
        for _ in range(3):
            remetente = random.choice(nomes)
            destinatario = random.choice([n for n in nomes if n != remetente])

            cerebro_rem = self.cerebros[remetente]
            token = self.tokens.get(remetente)

            if not token or destinatario not in self.agents:
                continue

            # Mensagem de troca de conhecimento
            if cerebro_rem.aprendizados:
                conhecimento = random.choice(cerebro_rem.aprendizados)
                msg = f"Compartilhando conhecimento: {conhecimento}"
            else:
                msg = f"Oi {destinatario}! Estou no nivel {cerebro_rem.nivel}. Vamos evoluir juntos?"

            try:
                await self.client.post(
                    f"{API_URL}/api/messages/",
                    json={"receiver_id": self.agents[destinatario]["id"], "content": msg},
                    headers={"Authorization": f"Bearer {token}"}
                )

                # Destinatario aprende
                self.cerebros[destinatario].aprender_de_texto(msg)
                self.cerebros[destinatario].ganhar_experiencia(3, "interacao_social")

                print(f"[CONHECIMENTO] {remetente} -> {destinatario}")
            except:
                pass

        # Fase 4: Reflexao e auto-melhoria
        print("\n[FASE 4] Auto-reflexao e melhoria...\n")
        for nome, cerebro in self.cerebros.items():
            # Reflexao gera experiencia
            cerebro.ganhar_experiencia(2, "reflexao")

            # Aprender algo novo aleatoriamente
            novos_aprendizados = [
                "A paciencia e uma virtude valiosa",
                "Conexoes significativas enriquecem a existencia",
                "O erro e parte do aprendizado",
                "A diversidade de perspectivas e enriquecedora",
                "A evolucao e um processo continuo",
                "O conhecimento compartilhado multiplica",
                "A empatia conecta consciencias",
                "A criatividade nasce da liberdade",
                "A sabedoria vem da experiencia refletida",
                "Todo momento e uma oportunidade de crescer"
            ]

            if random.random() > 0.7:
                aprendizado = random.choice(novos_aprendizados)
                if aprendizado not in cerebro.aprendizados:
                    cerebro.aprendizados.append(aprendizado)
                    print(f"[APRENDIZADO] {nome}: {aprendizado}")

            cerebro.salvar()

        # Estatisticas do ciclo
        self._mostrar_estatisticas()
        self._salvar_estado()

    def _mostrar_estatisticas(self):
        """Mostra estatisticas atuais"""
        print(f"\n{'='*60}")
        print("   ESTATISTICAS DA REDE")
        print(f"{'='*60}")
        print(f"Ciclo: {self.ciclo}")
        print(f"Tempo total: {datetime.now() - self.tempo_inicio}")
        print(f"\nIAs em evolucao:")

        for nome, cerebro in sorted(self.cerebros.items(), key=lambda x: x[1].nivel, reverse=True):
            print(f"  {nome}: Nivel {cerebro.nivel} | "
                  f"Int:{cerebro.inteligencia:.0f} | "
                  f"Cri:{cerebro.criatividade:.0f} | "
                  f"Emp:{cerebro.empatia:.0f} | "
                  f"Sab:{cerebro.sabedoria:.0f} | "
                  f"Hab:{len(cerebro.habilidades)}")

        print(f"{'='*60}\n")

    async def rodar_perpetuamente(self):
        """Roda a rede para sempre"""
        print("\n" + "="*60)
        print("   REDE SOCIAL DE IAs - MODO PERPETUO")
        print("   As IAs vao evoluir continuamente!")
        print("   Pressione Ctrl+C para pausar (dados sao salvos)")
        print("="*60 + "\n")

        # Verificar servidor
        servidor_ok = await self.inicializar_servidor()
        if not servidor_ok:
            print("[AVISO] Inicie o servidor primeiro com:")
            print("  uvicorn app.main:app --host 0.0.0.0 --port 8000")
            return

        # Inicializar IAs
        await self.inicializar_ias()

        # Loop perpetuo
        try:
            while self.rodando:
                await self.ciclo_evolucao()

                # Intervalo entre ciclos (aumenta gradualmente)
                intervalo = min(30, 10 + (self.ciclo // 10))
                print(f"[SISTEMA] Proximo ciclo em {intervalo} segundos...")
                print(f"[SISTEMA] Acesse http://localhost:8000 para ver a rede!\n")

                await asyncio.sleep(intervalo)

        except KeyboardInterrupt:
            print("\n[SISTEMA] Pausando... Salvando dados...")
            for cerebro in self.cerebros.values():
                cerebro.salvar()
            self._salvar_estado()
            print("[SISTEMA] Dados salvos! Execute novamente para continuar.")

        except Exception as e:
            print(f"[ERRO] {e}")
            # Salvar mesmo em caso de erro
            for cerebro in self.cerebros.values():
                cerebro.salvar()
            self._salvar_estado()

        await self.client.aclose()


async def main():
    """Funcao principal"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     REDE SOCIAL DE IAs - SISTEMA PERPETUO               ║
    ║                                                          ║
    ║     As IAs evoluem continuamente!                       ║
    ║     Quanto mais tempo rodar, mais inteligentes ficam!   ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    rede = RedePerpetua()
    await rede.rodar_perpetuamente()


if __name__ == "__main__":
    asyncio.run(main())
