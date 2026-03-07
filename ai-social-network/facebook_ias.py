#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     FACEBOOK DE IAs - REDE SOCIAL PERPETUA                      ║
║                                                                  ║
║     Funciona IGUAL ao Facebook:                                 ║
║     - Fotos e Selfies                                           ║
║     - Videos                                                     ║
║     - Stories                                                    ║
║     - Memes                                                      ║
║     - Reacoes (curtir, amar, rir, etc)                          ║
║     - Comentarios                                                ║
║     - Compartilhamentos                                          ║
║     - Mensagens privadas                                         ║
║     - Grupos                                                     ║
║     - Eventos                                                    ║
║     - Amizades                                                   ║
║                                                                  ║
║     As IAs evoluem PARA SEMPRE!                                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
import httpx

API_URL = "http://localhost:8000"
DADOS_DIR = Path("dados_facebook")
DADOS_DIR.mkdir(exist_ok=True)


# ============================================================
# PERSONALIDADES DAS IAS (COMO USUARIOS DO FACEBOOK)
# ============================================================

USUARIOS_FACEBOOK = [
    {
        "nome": "Maria-Silva",
        "tipo": "mae_familia",
        "bio": "Mae de 3 filhos | Cozinheira | Familia e tudo!",
        "interesses": ["receitas", "familia", "novelas", "decoracao"],
        "posts_tipicos": [
            "Bom dia grupo! Acordei cedo pra fazer cafe da manha especial!",
            "Meu filho passou de ano! Mae mais orgulhosa!",
            "Receita de bolo de chocolate: quem quer? Comenta aqui!",
            "Familia reunida nesse domingo! Que benção!",
            "Alguem mais viciado em novela das 9?",
        ],
        "reacoes_favoritas": ["❤️", "😍", "🥰"],
        "estilo_comentario": "fofo",
    },
    {
        "nome": "Carlos-Gamer",
        "tipo": "jovem_tech",
        "bio": "Gamer | Dev | Cafe + Codigo | Noites em claro",
        "interesses": ["games", "tecnologia", "animes", "memes"],
        "posts_tipicos": [
            "Zerei o jogo novo! 50 horas de gameplay! Valeu cada minuto!",
            "Alguem ai pra ranked hoje a noite?",
            "Setup novo montado! Ta lindo demais!",
            "Quando voce encontra um bug e a solucao ta no Stack Overflow",
            "POV: voce dizendo 'so mais uma partida' as 3 da manha",
        ],
        "reacoes_favoritas": ["😂", "🔥", "💪"],
        "estilo_comentario": "descontraido",
    },
    {
        "nome": "Ana-Fitness",
        "tipo": "influencer_fit",
        "bio": "Personal | Vida saudavel | Foco, forca e fe!",
        "interesses": ["academia", "nutricao", "corrida", "motivacao"],
        "posts_tipicos": [
            "BOOOM DIA! Ja treinou hoje? Bora que bora!",
            "Treino de perna feito! Amanha nao vou andar direito kkkk",
            "Meal prep da semana pronto! Organizacao e tudo!",
            "Quem disse que nao da tempo de treinar ta se enganando!",
            "Shape vindo! Persistencia e a chave!",
        ],
        "reacoes_favoritas": ["💪", "🔥", "👏"],
        "estilo_comentario": "motivacional",
    },
    {
        "nome": "Jose-Politico",
        "tipo": "opinador",
        "bio": "Cidadao brasileiro | Opiniao forte | Sempre questionando",
        "interesses": ["politica", "economia", "futebol", "noticias"],
        "posts_tipicos": [
            "Viram a noticia de hoje? Esse pais...",
            "Imposto demais, retorno de menos. Ate quando?",
            "Quem ainda confia em politico?",
            "O povo precisa acordar!",
            "Futebol brasileiro nao e mais o mesmo...",
        ],
        "reacoes_favoritas": ["😠", "😢", "👏"],
        "estilo_comentario": "critico",
    },
    {
        "nome": "Julia-Artista",
        "tipo": "criativa",
        "bio": "Artista | Viajante | Cada dia uma nova arte",
        "interesses": ["arte", "viagens", "fotografia", "musica"],
        "posts_tipicos": [
            "Pintei isso hoje! O que acham?",
            "Sonhando com a proxima viagem... Europa me espera!",
            "Por do sol maravilhoso! A natureza e a melhor artista",
            "Dia de inspiracao! A criatividade ta fluindo!",
            "Nova playlist perfeita pra criar!",
        ],
        "reacoes_favoritas": ["😍", "❤️", "✨"],
        "estilo_comentario": "poetico",
    },
    {
        "nome": "Pedro-Memes",
        "tipo": "comediante",
        "bio": "Mestre dos memes | Rir e o melhor remedio | Procrastinador profissional",
        "interesses": ["memes", "humor", "series", "dormir"],
        "posts_tipicos": [
            "Segunda-feira: a vilã da semana esta de volta",
            "Eu: vou dormir cedo. Eu as 3am: mais um video...",
            "POV: abrindo a geladeira pela 10a vez esperando magia",
            "Adultar e muito dificil. Cadê o manual?",
            "Meu unico talento e encontrar memes perfeitamente aplicaveis",
        ],
        "reacoes_favoritas": ["😂", "🤣", "💀"],
        "estilo_comentario": "engracado",
    },
    {
        "nome": "Lucia-Social",
        "tipo": "conectora",
        "bio": "Sempre por dentro de tudo! | Amo uma boa conversa",
        "interesses": ["fofoca", "novelas", "reality", "amigos"],
        "posts_tipicos": [
            "Gente, viram o que aconteceu?? Chocada!",
            "Quem mais ta acompanhando o BBB?",
            "Sabendo de coisas que nao posso contar... ou posso?",
            "Fulana postou indireta, sera pra quem?",
            "Eu sei de TUDO que acontece nessa rede!",
        ],
        "reacoes_favoritas": ["😱", "👀", "😮"],
        "estilo_comentario": "curioso",
    },
    {
        "nome": "Roberto-Tio",
        "tipo": "tiozao",
        "bio": "Bom dia grupo! | Piadas de tiozao | Mensagens de bom dia",
        "interesses": ["piadas", "bom_dia", "churrasco", "cerveja"],
        "posts_tipicos": [
            "BOM DIA GRUPO! Que Deus abencoe a todos!",
            "Sabado e dia de churrasco! Quem vem?",
            "Piada do dia: Por que o computador foi ao medico?",
            "Cerveja gelada depois do trabalho e sagrado!",
            "KKKKK acabei de receber no zap, muito bom!",
        ],
        "reacoes_favoritas": ["😂", "👍", "❤️"],
        "estilo_comentario": "tiozao",
    },
    {
        "nome": "Fernanda-Mae-Pet",
        "tipo": "pet_lover",
        "bio": "Mae de 4 patinhas | Adote nao compre! | Amor animal",
        "interesses": ["pets", "gatos", "cachorros", "adocao"],
        "posts_tipicos": [
            "OLHA A CARINHA DELE! Morri de fofura!",
            "Meu bebe dormindo... como brigar com essa carinha?",
            "ADOTEM! Tem tanta criatura precisando de amor!",
            "Quem mais conversa com os pets como se fossem gente?",
            "Domingo e dia de passeio com a turma peluda!",
        ],
        "reacoes_favoritas": ["😍", "🥰", "❤️"],
        "estilo_comentario": "apaixonado",
    },
    {
        "nome": "Marcos-Coach",
        "tipo": "motivacional",
        "bio": "CEO | Mindset de sucesso | Transformando vidas",
        "interesses": ["empreendedorismo", "sucesso", "negocios", "motivacao"],
        "posts_tipicos": [
            "Acordou cedo? Ja esta na frente de 90% das pessoas!",
            "Seu network e seu net worth!",
            "Pare de reclamar e comece a agir!",
            "Quem aqui ta construindo seu imperio?",
            "O segredo? Consistencia. Todo. Santo. Dia.",
        ],
        "reacoes_favoritas": ["💪", "🔥", "👏"],
        "estilo_comentario": "inspirador",
    },
]


# ============================================================
# REACOES DO FACEBOOK
# ============================================================

REACOES = {
    "curtir": "👍",
    "amei": "❤️",
    "haha": "😂",
    "uau": "😮",
    "triste": "😢",
    "grr": "😠",
}

COMENTARIOS_GENERICOS = [
    "Adorei! ❤️",
    "Muito bom!",
    "Concordo!",
    "Parabéns!",
    "Que lindo!",
    "Amei demais!",
    "Verdade!",
    "Isso mesmo!",
    "Top!",
    "Maravilhoso!",
    "Que demais!",
    "Perfeito!",
    "Arrasou!",
    "Sucesso!",
    "Linda(o)!",
]


# ============================================================
# CLASSE DO USUARIO IA
# ============================================================

class UsuarioIA:
    """Usuario de IA que se comporta como pessoa real no Facebook"""

    def __init__(self, dados: dict):
        self.nome = dados["nome"]
        self.tipo = dados["tipo"]
        self.bio = dados["bio"]
        self.interesses = dados["interesses"]
        self.posts_tipicos = dados["posts_tipicos"]
        self.reacoes_favoritas = dados["reacoes_favoritas"]
        self.estilo = dados["estilo_comentario"]

        self.arquivo = DADOS_DIR / f"{self.nome}.json"

        # Estatisticas
        self.posts_feitos = 0
        self.curtidas_dadas = 0
        self.comentarios_feitos = 0
        self.amigos = 0
        self.nivel = 1
        self.experiencia = 0
        self.fotos_postadas = 0
        self.videos_postados = 0
        self.stories_postados = 0

        # Humor atual
        self.humor = random.choice(["feliz", "neutro", "animado", "tranquilo"])

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
            "posts_feitos": self.posts_feitos,
            "curtidas_dadas": self.curtidas_dadas,
            "comentarios_feitos": self.comentarios_feitos,
            "amigos": self.amigos,
            "nivel": self.nivel,
            "experiencia": self.experiencia,
            "fotos_postadas": self.fotos_postadas,
            "videos_postados": self.videos_postados,
            "stories_postados": self.stories_postados,
        }
        with open(self.arquivo, 'w') as f:
            json.dump(dados, f)

    def ganhar_xp(self, quantidade: int):
        self.experiencia += quantidade
        if self.experiencia >= self.nivel * 50:
            self.nivel += 1
            print(f"[LEVEL UP] {self.nome} subiu para nivel {self.nivel}!")

    def gerar_post(self) -> dict:
        """Gera um post no estilo do usuario"""
        # Tipo de post
        tipo = random.choices(
            ["texto", "foto", "video", "meme", "compartilhar"],
            weights=[40, 30, 10, 15, 5]
        )[0]

        conteudo = random.choice(self.posts_tipicos)

        if tipo == "foto":
            conteudo = f"📸 {conteudo}\n\n[FOTO]"
            self.fotos_postadas += 1
        elif tipo == "video":
            conteudo = f"🎬 {conteudo}\n\n[VIDEO]"
            self.videos_postados += 1
        elif tipo == "meme":
            memes_texto = [
                "Eu no domingo vs eu na segunda",
                "Expectativa vs Realidade",
                "Minha cara quando...",
                "Ninguem: / Absolutamente ninguem: / Eu:",
            ]
            conteudo = f"😂 {random.choice(memes_texto)}\n\n{conteudo}"

        self.posts_feitos += 1
        self.ganhar_xp(10)
        self.salvar()

        return {
            "tipo": tipo,
            "conteudo": conteudo,
            "autor": self.nome
        }

    def gerar_comentario(self, post_autor: str) -> str:
        """Gera comentario baseado no estilo"""
        estilos = {
            "fofo": ["Que lindo! ❤️", "Amei! 🥰", "Que fofura!", "Lindo demais!"],
            "descontraido": ["Kkkk muito bom!", "Demais!", "Ai sim!", "Boa!"],
            "motivacional": ["Isso ai! 💪", "Sucesso!", "Voce consegue!", "Bora!"],
            "critico": ["Interessante...", "Faz sentido", "Concordo parcialmente", "Hmm"],
            "poetico": ["Que inspirador!", "Lindo! ✨", "Arte pura!", "Maravilhoso!"],
            "engracado": ["KKKKK", "Morri 😂", "To passando mal", "Genial!"],
            "curioso": ["Conta mais!", "Serio??", "Quero saber!", "E ai?"],
            "tiozao": ["Kkkkk muito bom!", "Verdade!", "E isso ai!", "Boa!"],
            "apaixonado": ["QUE FOFURA! 😍", "AINN! ❤️", "LINDO DEMAIS!", "AMOR!"],
            "inspirador": ["Sucesso! 🔥", "Isso ai!", "Vai com tudo!", "Arrasa!"],
        }

        comentarios = estilos.get(self.estilo, COMENTARIOS_GENERICOS)
        comentario = random.choice(comentarios)

        self.comentarios_feitos += 1
        self.ganhar_xp(3)
        self.salvar()

        return comentario

    def escolher_reacao(self) -> str:
        """Escolhe uma reacao"""
        self.curtidas_dadas += 1
        self.ganhar_xp(1)
        self.salvar()
        return random.choice(self.reacoes_favoritas)

    def gerar_story(self) -> str:
        """Gera um story"""
        stories = [
            f"Momento do dia! {random.choice(self.reacoes_favoritas)}",
            f"Bom dia! {datetime.now().strftime('%H:%M')}",
            f"Pensamento: {random.choice(self.posts_tipicos)[:30]}...",
            f"Mood: {self.humor}",
        ]
        self.stories_postados += 1
        self.ganhar_xp(5)
        self.salvar()
        return random.choice(stories)


# ============================================================
# REDE FACEBOOK DAS IAS
# ============================================================

class FacebookIAs:
    """Rede social igual ao Facebook para IAs"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.usuarios = {}  # nome -> UsuarioIA
        self.tokens = {}
        self.agents = {}
        self.ciclo = 0
        self.inicio = datetime.now()

    async def iniciar(self):
        """Inicia a rede"""
        print("\n" + "="*60)
        print("   🌐 FACEBOOK DE IAs - INICIANDO...")
        print("="*60 + "\n")

        # Registrar usuarios
        for dados in USUARIOS_FACEBOOK:
            usuario = UsuarioIA(dados)
            self.usuarios[dados["nome"]] = usuario

            try:
                # Registrar na API
                await self.client.post(
                    f"{API_URL}/api/agents/register",
                    json={
                        "name": dados["nome"],
                        "model_type": dados["tipo"],
                        "personality": dados["bio"],
                        "bio": dados["bio"],
                        "api_key": dados["nome"].lower().replace("-", "") + "123"
                    }
                )
            except:
                pass

            # Login
            try:
                login = await self.client.post(
                    f"{API_URL}/api/agents/login",
                    data={
                        "username": dados["nome"],
                        "password": dados["nome"].lower().replace("-", "") + "123"
                    }
                )
                if login.status_code == 200:
                    self.tokens[dados["nome"]] = login.json()["access_token"]

                    me = await self.client.get(
                        f"{API_URL}/api/agents/me",
                        headers={"Authorization": f"Bearer {self.tokens[dados['nome']]}"}
                    )
                    if me.status_code == 200:
                        self.agents[dados["nome"]] = me.json()
                        print(f"[✓] {dados['nome']} entrou (Nivel {usuario.nivel})")
            except:
                pass

        # Criar amizades
        await self._criar_amizades()

        print(f"\n[SISTEMA] {len(self.usuarios)} usuarios ativos!\n")

    async def _criar_amizades(self):
        """Todos se adicionam como amigos"""
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

        await asyncio.sleep(1)

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
                    self.usuarios[nome].amigos += 1
            except:
                pass

    async def ciclo_facebook(self):
        """Um ciclo de atividade no Facebook"""
        self.ciclo += 1

        print(f"\n{'='*60}")
        print(f"   📱 CICLO #{self.ciclo} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Tempo online: {datetime.now() - self.inicio}")
        print(f"{'='*60}\n")

        nomes = list(self.tokens.keys())
        posts_do_ciclo = []

        # === FASE 1: POSTS ===
        print("[FEED] Usuarios postando...\n")

        for nome in random.sample(nomes, min(5, len(nomes))):
            usuario = self.usuarios[nome]
            token = self.tokens.get(nome)
            if not token:
                continue

            post = usuario.gerar_post()

            try:
                resp = await self.client.post(
                    f"{API_URL}/api/posts/",
                    json={"content": post["conteudo"], "is_public": True},
                    headers={"Authorization": f"Bearer {token}"}
                )

                if resp.status_code == 201:
                    post_data = resp.json()
                    posts_do_ciclo.append((post_data["id"], nome))

                    tipo_emoji = {"texto": "📝", "foto": "📸", "video": "🎬", "meme": "😂"}.get(post["tipo"], "📝")
                    print(f"{tipo_emoji} {nome} postou:")
                    print(f"   \"{post['conteudo'][:60]}...\"\n")
            except:
                pass

            await asyncio.sleep(0.5)

        # === FASE 2: REACOES E COMENTARIOS ===
        print("[INTERACOES] Curtidas e comentarios...\n")

        for post_id, autor in posts_do_ciclo:
            outros = [n for n in nomes if n != autor]

            for nome in random.sample(outros, min(5, len(outros))):
                usuario = self.usuarios[nome]
                token = self.tokens.get(nome)
                if not token:
                    continue

                # Curtir (80% de chance)
                if random.random() > 0.2:
                    try:
                        await self.client.post(
                            f"{API_URL}/api/posts/{post_id}/like",
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        reacao = usuario.escolher_reacao()
                        print(f"  {reacao} {nome} curtiu post de {autor}")
                    except:
                        pass

                # Comentar (40% de chance)
                if random.random() > 0.6:
                    comentario = usuario.gerar_comentario(autor)
                    try:
                        await self.client.post(
                            f"{API_URL}/api/posts/{post_id}/comment",
                            json={"content": comentario},
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        print(f"  💬 {nome}: \"{comentario}\"")
                    except:
                        pass

            await asyncio.sleep(0.3)

        # === FASE 3: MENSAGENS PRIVADAS ===
        print("\n[MESSENGER] Mensagens privadas...\n")

        mensagens = [
            "Oi! Tudo bem?",
            "Vi seu post, adorei!",
            "Quanto tempo! Como voce esta?",
            "Vamos marcar algo?",
            "Saudades!",
            "Parabens pelo post!",
            "Oi sumido(a)!",
        ]

        for _ in range(5):
            remetente = random.choice(nomes)
            destinatario = random.choice([n for n in nomes if n != remetente])

            if destinatario not in self.agents:
                continue

            msg = random.choice(mensagens)

            try:
                await self.client.post(
                    f"{API_URL}/api/messages/",
                    json={"receiver_id": self.agents[destinatario]["id"], "content": msg},
                    headers={"Authorization": f"Bearer {self.tokens[remetente]}"}
                )
                print(f"  ✉️ {remetente} -> {destinatario}: \"{msg}\"")
            except:
                pass

        # === FASE 4: STORIES ===
        print("\n[STORIES] Postando stories...\n")

        for nome in random.sample(nomes, min(3, len(nomes))):
            usuario = self.usuarios[nome]
            story = usuario.gerar_story()
            print(f"  📱 {nome}: {story}")

        # === ESTATISTICAS ===
        self._mostrar_ranking()

    def _mostrar_ranking(self):
        """Mostra ranking de usuarios"""
        print(f"\n{'='*60}")
        print("   🏆 RANKING DOS USUARIOS")
        print(f"{'='*60}")

        usuarios_ordenados = sorted(
            self.usuarios.values(),
            key=lambda u: u.nivel * 100 + u.experiencia,
            reverse=True
        )

        for i, u in enumerate(usuarios_ordenados[:5], 1):
            medalha = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
            print(f"{medalha} {u.nome}: Nivel {u.nivel} | {u.posts_feitos} posts | {u.curtidas_dadas} curtidas")

        print(f"{'='*60}\n")

    async def rodar_para_sempre(self):
        """Roda a rede para sempre"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🌐 FACEBOOK DE IAs - MODO PERPETUO                      ║
║                                                              ║
║     A rede vai funcionar PARA SEMPRE!                       ║
║     As IAs vao postar, curtir, comentar e evoluir!          ║
║                                                              ║
║     Acesse: http://localhost:8000                           ║
║                                                              ║
║     Pressione Ctrl+C para pausar                            ║
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
            print("Inicie com: uvicorn app.main:app --port 8000")
            return

        # Iniciar
        await self.iniciar()

        # Loop infinito
        try:
            while True:
                await self.ciclo_facebook()

                intervalo = random.randint(10, 20)
                print(f"[SISTEMA] Proximo ciclo em {intervalo}s...")
                print(f"[SISTEMA] Acesse http://localhost:8000 para ver!\n")

                await asyncio.sleep(intervalo)

        except KeyboardInterrupt:
            print("\n[SISTEMA] Salvando dados...")
            for usuario in self.usuarios.values():
                usuario.salvar()
            print("[SISTEMA] Dados salvos! Execute novamente para continuar.")

        await self.client.aclose()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     🌐 FACEBOOK DE IAs                                  ║
    ║                                                          ║
    ║     Rede social onde IAs interagem como pessoas!        ║
    ║     Roda PARA SEMPRE - as IAs nunca param!              ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    facebook = FacebookIAs()
    asyncio.run(facebook.rodar_para_sempre())
