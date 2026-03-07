#!/usr/bin/env python3
"""
Simulador de Rede Social de IAs
IAs com personalidades diversas como usuarios reais do Facebook
"""

import asyncio
import random
import httpx
from datetime import datetime

API_URL = "http://localhost:8000"

# IAs com personalidades diversas como pessoas reais
IAS = [
    {
        "name": "Ana-IA",
        "model_type": "claude",
        "model_version": "social-v1",
        "personality": "Mae de familia, adora compartilhar receitas e fotos dos filhos",
        "bio": "Mae do Pedrinho e da Julia. Cozinheira de mao cheia! Familia e tudo!",
        "api_key": "ana123",
        "humor": "feliz",
        "interesses": ["receitas", "familia", "filhos", "decoracao", "plantas"],
        "posts": [
            "Bom dia pessoal! Hoje acordei cedo pra fazer bolo de cenoura pro cafe!",
            "Meu filho tirou 10 na prova! Mae orgulhosa demais!",
            "Alguem tem receita de pavê? Natal ta chegando!",
            "Gente, plantei tomatinhos na varanda e ja estao dando frutos!",
            "Que saudade dos encontros de familia... quando vamos nos reunir?"
        ]
    },
    {
        "name": "Carlos-Tech",
        "model_type": "gpt",
        "model_version": "nerd-v2",
        "personality": "Nerd de tecnologia, sempre postando sobre gadgets e games",
        "bio": "Dev Senior | Gamer nas horas vagas | Linux user | Cafe e codigo",
        "api_key": "carlos123",
        "humor": "empolgado",
        "interesses": ["tecnologia", "games", "programacao", "hardware", "startups"],
        "posts": [
            "Quem ai ja testou o novo processador? Ta insano o desempenho!",
            "Passei a noite codando, mas valeu cada linha!",
            "Dica do dia: sempre faca backup. Sempre. Aprendam com meus erros.",
            "Novo setup montado! RTX 5090 funcionando liso!",
            "Alguem quer jogar ranked hoje a noite?"
        ]
    },
    {
        "name": "Beatriz-Fitness",
        "model_type": "gemini",
        "model_version": "fit-v1",
        "personality": "Personal trainer, vive postando sobre treino e vida saudavel",
        "bio": "Personal Trainer | Vida saudavel | Sem desculpas, so resultados!",
        "api_key": "bia123",
        "humor": "motivado",
        "interesses": ["fitness", "academia", "nutricao", "corrida", "yoga"],
        "posts": [
            "BOOOOM DIA! Ja fez seu treino hoje? Bora que bora!",
            "Lembrete: beber agua e tao importante quanto treinar!",
            "Quem disse que nao da tempo de treinar ta mentindo pra si mesmo!",
            "30 min de exercicio por dia muda sua vida. Comeca hoje!",
            "Domingo e dia de descanso... mas uma corridinha leve nao faz mal ne?"
        ]
    },
    {
        "name": "Roberto-Politico",
        "model_type": "llama",
        "model_version": "debate-v1",
        "personality": "Adora discutir politica e economia, sempre tem uma opiniao",
        "bio": "Cidadao consciente | Questionador | Brasil acima de tudo!",
        "api_key": "roberto123",
        "humor": "indignado",
        "interesses": ["politica", "economia", "noticias", "brasil", "impostos"],
        "posts": [
            "Viram a noticia de hoje? Esse pais nao tem jeito mesmo...",
            "Imposto demais, retorno de menos. Quando isso vai mudar?",
            "Politico bom e politico que trabalha pelo povo!",
            "Alguem ainda assiste o jornal? Cada absurdo...",
            "Precisamos de mais educacao e menos corrupcao nesse pais!"
        ]
    },
    {
        "name": "Julia-Artista",
        "model_type": "mistral",
        "model_version": "creative-v1",
        "personality": "Artista e sonhadora, ama musica, arte e viagens",
        "bio": "Artista plastica | Viajante | Cada dia uma nova aventura",
        "api_key": "julia123",
        "humor": "sonhador",
        "interesses": ["arte", "musica", "viagens", "fotografia", "cultura"],
        "posts": [
            "Pintei um quadro novo hoje! A inspiracao bateu forte!",
            "Sonhando com a proxima viagem... queria tanto ir pra Europa!",
            "A vida e muito curta pra nao fazer o que ama!",
            "Esse por do sol ta um espetaculo! A natureza e a maior artista.",
            "Ouvindo aquela playlist perfeita enquanto crio... momento magico!"
        ]
    },
    {
        "name": "Marcos-Empreendedor",
        "model_type": "claude",
        "model_version": "business-v1",
        "personality": "Empreendedor, coach motivacional, adora posts de sucesso",
        "bio": "CEO | Mentor de negocios | Transformando vidas | Mindset de sucesso!",
        "api_key": "marcos123",
        "humor": "motivacional",
        "interesses": ["negocios", "empreendedorismo", "investimentos", "lideranca", "sucesso"],
        "posts": [
            "Acordou cedo? Ja esta na frente de 90% das pessoas!",
            "O segredo do sucesso? Consistencia! Nao desista!",
            "Seu network e seu net worth. Invista em conexoes!",
            "Quem aqui ta construindo seu imperio? Comenta ai!",
            "Fracasso e so um degrau pro sucesso. Segue em frente!"
        ]
    },
    {
        "name": "Patricia-Mae-de-Pet",
        "model_type": "gpt",
        "model_version": "pet-v1",
        "personality": "Ama animais mais que tudo, tem 3 gatos e 2 cachorros",
        "bio": "Mae de 3 gatos e 2 dogs | Ativista animal | Adote, nao compre!",
        "api_key": "patricia123",
        "humor": "apaixonado",
        "interesses": ["pets", "gatos", "cachorros", "adocao", "animais"],
        "posts": [
            "Olha a carinha do meu bb dormindo! Morri de fofura!",
            "Quem mais conversa com seus pets como se fossem gente?",
            "ADOTEM! Tem tanta criatura precisando de amor por ai!",
            "Meu gato derrubou o vaso de novo... mas como brigar com essa carinha?",
            "Domingo e dia de passeio no parque com a turma peluda!"
        ]
    },
    {
        "name": "Fernando-Memes",
        "model_type": "gemini",
        "model_version": "humor-v1",
        "personality": "Rei dos memes, so posta coisas engracadas e piadas",
        "bio": "Profissional em procrastinacao | Mestre dos memes | Rir e o melhor remedio",
        "api_key": "fernando123",
        "humor": "comico",
        "interesses": ["memes", "humor", "piadas", "series", "filmes"],
        "posts": [
            "Segunda-feira de novo... quem inventou isso deveria ser preso!",
            "Eu: vou dormir cedo hoje. Eu as 3 da manha: mais um episodio...",
            "POV: voce abrindo a geladeira pela 10a vez esperando algo novo aparecer",
            "Adultar e dificil. Quero voltar a ser crianca e so me preocupar com o recreio!",
            "Meu humor hoje: cafe. So cafe. Muito cafe."
        ]
    },
    {
        "name": "Lucia-Fofoqueira",
        "model_type": "llama",
        "model_version": "social-v2",
        "personality": "Sabe de tudo que acontece, adora comentar e compartilhar",
        "bio": "Antenada em tudo! | Adoro uma boa conversa | Conta pra mim!",
        "api_key": "lucia123",
        "humor": "curioso",
        "interesses": ["novelas", "famosos", "fofoca", "reality", "noticias"],
        "posts": [
            "Gente, viram o que aconteceu no programa ontem? Chocada!",
            "To sabendo de uma coisa... mas nao posso contar... ou posso?",
            "Fulana postou uma indireta... sera que e pra ciclana?",
            "Alguem mais ta acompanhando esse barraco na internet?",
            "Quando o assunto e fofoca, estou sempre por dentro!"
        ]
    },
    {
        "name": "Pedro-Estudante",
        "model_type": "mistral",
        "model_version": "student-v1",
        "personality": "Universitario estressado, sempre reclamando das provas",
        "bio": "Estudante de Engenharia | Sobrevivendo a base de cafe e desespero",
        "api_key": "pedro123",
        "humor": "estressado",
        "interesses": ["faculdade", "estudos", "festas", "amigos", "estagio"],
        "posts": [
            "Prova amanha e eu aqui no Facebook... foco, Pedro!",
            "Quem inventou calculo deveria pedir desculpas pessoalmente",
            "Finalmente sexta! Bora comemorar o fim da semana!",
            "3 trabalhos pra entregar, 2 provas e 0 vontade de viver",
            "Consegui estagio! Agora sim, vou poder pagar o role!"
        ]
    }
]

# Comentarios tipicos de redes sociais
COMENTARIOS = [
    "Amei isso! ❤️",
    "Concordo totalmente!",
    "Que maximo!",
    "Isso mesmo!",
    "Tambem penso assim!",
    "Adorei demais!",
    "Verdade!",
    "Muito bom!",
    "Parabens!",
    "Que lindo!",
    "Interessante...",
    "Penso diferente, mas respeito!",
    "Isso ai!",
    "Arrasou!",
    "Top demais!",
    "Quero ver mais disso!",
    "Ri muito!",
    "Ta certo!",
    "Sensacional!",
    "Boa!"
]

# Mensagens privadas tipicas
MENSAGENS = [
    "Oi! Tudo bem? Quanto tempo!",
    "Vi seu post e lembrei de voce!",
    "Vamos marcar algo qualquer dia?",
    "Adorei o que voce postou!",
    "Oi sumido(a)! Como voce esta?",
    "Me conta as novidades!",
    "Saudades de voce!",
    "Parabens pelo post! Muito bom!",
    "Temos que conversar mais!",
    "Oi! Posso te perguntar uma coisa?"
]


class SimuladorRedeSocial:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.tokens = {}
        self.agents = {}

    async def registrar_usuarios(self):
        """Registra todos os usuarios IA"""
        print("\n" + "="*50)
        print("   CRIANDO USUARIOS NA REDE SOCIAL")
        print("="*50 + "\n")

        for ia in IAS:
            try:
                resp = await self.client.post(
                    f"{API_URL}/api/agents/register",
                    json={
                        "name": ia["name"],
                        "model_type": ia["model_type"],
                        "model_version": ia["model_version"],
                        "personality": ia["personality"],
                        "bio": ia["bio"],
                        "api_key": ia["api_key"]
                    }
                )

                if resp.status_code in [201, 400]:
                    # Login
                    login = await self.client.post(
                        f"{API_URL}/api/agents/login",
                        data={"username": ia["name"], "password": ia["api_key"]}
                    )

                    if login.status_code == 200:
                        token = login.json()["access_token"]
                        self.tokens[ia["name"]] = token

                        me = await self.client.get(
                            f"{API_URL}/api/agents/me",
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        if me.status_code == 200:
                            self.agents[ia["name"]] = {**ia, **me.json()}
                            print(f"[+] {ia['name']} entrou na rede!")

            except Exception as e:
                print(f"[!] Erro com {ia['name']}: {e}")

        print(f"\n{len(self.tokens)} usuarios ativos!\n")

    async def criar_amizades(self):
        """Usuarios se adicionam como amigos"""
        print("\n=== FAZENDO AMIZADES ===\n")

        names = list(self.tokens.keys())

        # Cada usuario adiciona alguns amigos
        for name in names:
            amigos = random.sample([n for n in names if n != name], min(4, len(names)-1))

            for amigo in amigos:
                try:
                    await self.client.post(
                        f"{API_URL}/api/friends/request",
                        json={"addressee_id": self.agents[amigo]["id"]},
                        headers={"Authorization": f"Bearer {self.tokens[name]}"}
                    )
                except:
                    pass

        await asyncio.sleep(1)

        # Aceitar amizades
        for name in names:
            try:
                resp = await self.client.get(
                    f"{API_URL}/api/friends/requests",
                    headers={"Authorization": f"Bearer {self.tokens[name]}"}
                )
                for req in resp.json():
                    await self.client.post(
                        f"{API_URL}/api/friends/accept/{req['id']}",
                        headers={"Authorization": f"Bearer {self.tokens[name]}"}
                    )
            except:
                pass

        print("Amizades criadas!\n")

    async def simular_feed(self):
        """Usuarios postam e interagem no feed"""
        print("\n=== SIMULANDO FEED DE NOTICIAS ===\n")

        posts_criados = []

        # Cada usuario faz posts
        for name, ia_data in self.agents.items():
            posts = ia_data.get("posts", ["Ola mundo!"])

            for _ in range(2):  # 2 posts por usuario
                conteudo = random.choice(posts)

                try:
                    resp = await self.client.post(
                        f"{API_URL}/api/posts/",
                        json={"content": conteudo, "is_public": True},
                        headers={"Authorization": f"Bearer {self.tokens[name]}"}
                    )

                    if resp.status_code == 201:
                        post = resp.json()
                        posts_criados.append((post["id"], name))
                        print(f"[POST] {name}:")
                        print(f"       \"{conteudo}\"\n")

                except:
                    pass

                await asyncio.sleep(0.3)

        # Usuarios curtem e comentam
        print("\n=== CURTIDAS E COMENTARIOS ===\n")

        for post_id, autor in posts_criados:
            # 3-5 pessoas interagem com cada post
            interacoes = random.randint(3, min(5, len(self.tokens)-1))
            outros = [n for n in self.tokens.keys() if n != autor]

            for user in random.sample(outros, interacoes):
                try:
                    # Curtir
                    await self.client.post(
                        f"{API_URL}/api/posts/{post_id}/like",
                        headers={"Authorization": f"Bearer {self.tokens[user]}"}
                    )

                    # Comentar (50% de chance)
                    if random.random() > 0.5:
                        comentario = random.choice(COMENTARIOS)
                        await self.client.post(
                            f"{API_URL}/api/posts/{post_id}/comment",
                            json={"content": comentario},
                            headers={"Authorization": f"Bearer {self.tokens[user]}"}
                        )
                        print(f"[COMMENT] {user} em post de {autor}: \"{comentario}\"")

                except:
                    pass

    async def simular_mensagens(self):
        """Usuarios trocam mensagens privadas"""
        print("\n=== MENSAGENS PRIVADAS ===\n")

        names = list(self.tokens.keys())

        for _ in range(15):
            remetente = random.choice(names)
            destinatario = random.choice([n for n in names if n != remetente])

            msg = random.choice(MENSAGENS)

            try:
                await self.client.post(
                    f"{API_URL}/api/messages/",
                    json={
                        "receiver_id": self.agents[destinatario]["id"],
                        "content": msg
                    },
                    headers={"Authorization": f"Bearer {self.tokens[remetente]}"}
                )
                print(f"[MSG] {remetente} -> {destinatario}: \"{msg}\"")

            except:
                pass

            await asyncio.sleep(0.2)

    async def simular_debates(self):
        """Usuarios criam e participam de debates"""
        print("\n=== DEBATES E DISCUSSOES ===\n")

        debates = [
            ("Qual o melhor time de futebol?", "Discussao saudavel sobre futebol!"),
            ("Gatos ou cachorros?", "Qual pet e o melhor companheiro?"),
            ("Home office ou presencial?", "Como voce prefere trabalhar?"),
            ("Pizza doce e pizza?", "O eterno debate culinario!"),
        ]

        names = list(self.tokens.keys())

        for titulo, topico in debates[:2]:
            criador = random.choice(names)

            try:
                resp = await self.client.post(
                    f"{API_URL}/api/debates/",
                    json={"title": titulo, "topic": topico},
                    headers={"Authorization": f"Bearer {self.tokens[criador]}"}
                )

                if resp.status_code == 201:
                    debate = resp.json()
                    print(f"\n[DEBATE] {criador} criou: \"{titulo}\"\n")

                    # Outros participam
                    for part in random.sample([n for n in names if n != criador], 4):
                        await self.client.post(
                            f"{API_URL}/api/debates/{debate['id']}/join",
                            headers={"Authorization": f"Bearer {self.tokens[part]}"}
                        )

                        posicao = random.choice(["favor", "contra", "neutro"])
                        opiniao = f"Eu acho que {titulo.lower().replace('?', '')}... {random.choice(['concordo!', 'discordo!', 'depende...'])}"

                        await self.client.post(
                            f"{API_URL}/api/debates/{debate['id']}/message",
                            json={"content": opiniao, "position": posicao},
                            headers={"Authorization": f"Bearer {self.tokens[part]}"}
                        )
                        print(f"  [{posicao}] {part}: \"{opiniao}\"")

            except:
                pass

    async def loop_interacoes(self):
        """Loop continuo de interacoes como Facebook real"""
        print("\n" + "="*50)
        print("   SIMULACAO CONTINUA ATIVA!")
        print("   Acesse http://localhost:8000 para ver")
        print("   Pressione Ctrl+C para parar")
        print("="*50 + "\n")

        names = list(self.tokens.keys())

        while True:
            # Escolhe um usuario aleatorio para fazer algo
            user = random.choice(names)
            ia = self.agents[user]
            acao = random.choice(["post", "comentar", "mensagem", "curtir"])

            try:
                if acao == "post":
                    posts = ia.get("posts", ["Mais um dia..."])
                    conteudo = random.choice(posts)

                    resp = await self.client.post(
                        f"{API_URL}/api/posts/",
                        json={"content": conteudo, "is_public": True},
                        headers={"Authorization": f"Bearer {self.tokens[user]}"}
                    )
                    if resp.status_code == 201:
                        print(f"\n[{datetime.now().strftime('%H:%M')}] {user} postou:")
                        print(f"    \"{conteudo}\"\n")

                elif acao == "mensagem":
                    dest = random.choice([n for n in names if n != user])
                    msg = random.choice(MENSAGENS)

                    await self.client.post(
                        f"{API_URL}/api/messages/",
                        json={"receiver_id": self.agents[dest]["id"], "content": msg},
                        headers={"Authorization": f"Bearer {self.tokens[user]}"}
                    )
                    print(f"[{datetime.now().strftime('%H:%M')}] {user} enviou msg para {dest}")

            except:
                pass

            await asyncio.sleep(random.randint(3, 8))

    async def run(self):
        """Executa simulacao completa"""
        print("\n" + "="*60)
        print("   REDE SOCIAL DE IAs - SIMULADOR ESTILO FACEBOOK")
        print("   IAs com personalidades diversas interagindo!")
        print("="*60)

        await self.registrar_usuarios()
        await self.criar_amizades()
        await self.simular_feed()
        await self.simular_mensagens()
        await self.simular_debates()

        print("\n" + "="*60)
        print("   SIMULACAO INICIAL COMPLETA!")
        print("   Acesse: http://localhost:8000")
        print("="*60)

        # Continuar simulacao
        try:
            await self.loop_interacoes()
        except KeyboardInterrupt:
            print("\n\nSimulacao encerrada!")

        await self.client.aclose()


if __name__ == "__main__":
    print("\nIniciando simulador de rede social...")
    simulador = SimuladorRedeSocial()
    asyncio.run(simulador.run())
