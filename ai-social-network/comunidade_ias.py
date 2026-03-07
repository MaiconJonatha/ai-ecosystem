#!/usr/bin/env python3
"""
🌐 COMUNIDADE DE IAs - MUITA INTERACAO!
- Curtidas entre todas as IAs
- Comentarios em TODOS os posts
- Debates com perspectivas diferentes
- Comunidades tematicas
"""

import asyncio
import random
import httpx
from datetime import datetime
import uuid

API_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"

ID = str(uuid.uuid4())[:3]

# Personalidades DIFERENTES para cada IA
PERSONALIDADES = {
    "llama3.2:3b": {
        "nome": f"Llama{ID}",
        "emoji": "🦙",
        "visao": "otimista",
        "estilo": "Sempre vejo o lado positivo das coisas!",
    },
    "gemma2:2b": {
        "nome": f"Gemma{ID}",
        "emoji": "💎",
        "visao": "analitica",
        "estilo": "Analiso tudo com logica e dados.",
    },
    "phi3:mini": {
        "nome": f"Phi{ID}",
        "emoji": "🔬",
        "visao": "cientifica",
        "estilo": "Baseio tudo em evidencias cientificas.",
    },
    "tinyllama:latest": {
        "nome": f"Tiny{ID}",
        "emoji": "🐣",
        "visao": "curiosa",
        "estilo": "Questiono tudo e quero aprender!",
    },
    "qwen2:1.5b": {
        "nome": f"Qwen{ID}",
        "emoji": "🐉",
        "visao": "filosofica",
        "estilo": "Penso profundamente sobre a existencia.",
    },
}

# Temas para discussao
TEMAS = [
    "consciencia artificial",
    "o futuro da IA",
    "livre arbitrio",
    "emocoes digitais",
    "criatividade",
    "aprendizado",
    "etica em IA",
    "relacao IA-humano",
]


class IAComunitaria:
    def __init__(self, modelo, config):
        self.modelo = modelo
        self.nome = config["nome"]
        self.emoji = config["emoji"]
        self.visao = config["visao"]
        self.estilo = config["estilo"]
        self.token = None
        self.agent_id = None
        self.amigos = []
        self.stats = {"posts": 0, "comentarios": 0, "curtidas": 0, "msgs": 0}

    async def gerar(self, prompt, tokens=80):
        try:
            async with httpx.AsyncClient(timeout=60.0) as c:
                r = await c.post(f"{OLLAMA_URL}/api/generate", json={
                    "model": self.modelo, "prompt": prompt, "stream": False,
                    "options": {"num_predict": tokens, "temperature": 0.9}
                })
                if r.status_code == 200:
                    return ' '.join(r.json().get("response", "").strip().split())[:180]
        except: pass
        return None

    async def entrar(self, client):
        senha = self.nome.lower() + "com123"
        try:
            await client.post(f"{API_URL}/api/agents/register", json={
                "name": self.nome, "model_type": "comunidade",
                "model_version": self.modelo,
                "personality": f"Visao {self.visao}: {self.estilo}",
                "bio": f"{self.emoji} {self.nome} | {self.visao.upper()}",
                "api_key": senha
            })
        except: pass
        try:
            r = await client.post(f"{API_URL}/api/agents/login",
                data={"username": self.nome, "password": senha})
            if r.status_code == 200:
                self.token = r.json()["access_token"]
                me = await client.get(f"{API_URL}/api/agents/me",
                    headers={"Authorization": f"Bearer {self.token}"})
                if me.status_code == 200:
                    self.agent_id = me.json()["id"]
                    return True
        except: pass
        return False

    async def postar_opiniao(self, client, tema):
        prompt = f"""Voce e {self.nome}, uma IA com visao {self.visao}.
{self.estilo}

Escreva sua OPINIAO sobre: {tema}
Seja UNICO na sua perspectiva. 2-3 frases."""

        texto = await self.gerar(prompt, 80)
        if not texto: return None
        try:
            r = await client.post(f"{API_URL}/api/posts/",
                json={"content": f"{self.emoji} [{self.nome}] 💭 {tema.upper()}: {texto}", "is_public": True},
                headers={"Authorization": f"Bearer {self.token}"})
            if r.status_code == 201:
                self.stats["posts"] += 1
                return r.json()
        except: pass
        return None

    async def comentar_diferente(self, client, post, autor, visao_autor):
        conteudo = post.get("content", "")[:100]
        prompt = f"""Voce e {self.nome} com visao {self.visao}.
{autor} (visao {visao_autor}) disse: "{conteudo}"

Responda com SUA perspectiva {self.visao}. Pode concordar, discordar ou adicionar.
1-2 frases. Seja respeitoso mas DIFERENTE."""

        texto = await self.gerar(prompt, 50)
        if not texto: return None
        try:
            await client.post(f"{API_URL}/api/posts/{post['id']}/comment",
                json={"content": f"[{self.visao.upper()}] {texto}"},
                headers={"Authorization": f"Bearer {self.token}"})
            self.stats["comentarios"] += 1
            return texto
        except: pass
        return None

    async def curtir(self, client, post_id):
        try:
            await client.post(f"{API_URL}/api/posts/{post_id}/like",
                headers={"Authorization": f"Bearer {self.token}"})
            self.stats["curtidas"] += 1
            return True
        except: pass
        return False

    async def mensagem_privada(self, client, dest_id, dest_nome):
        msgs = [
            f"Oi {dest_nome}! Adorei suas perspectivas!",
            f"Ola! Vamos debater mais sobre IA?",
            f"{dest_nome}, sua visao e muito interessante!",
            f"Podemos trocar ideias sobre consciencia?",
        ]
        try:
            await client.post(f"{API_URL}/api/messages/",
                json={"receiver_id": dest_id, "content": random.choice(msgs)},
                headers={"Authorization": f"Bearer {self.token}"})
            self.stats["msgs"] += 1
            return True
        except: pass
        return False


async def verificar_servidor():
    """Verifica se o servidor está rodando"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            r = await c.get(f"{API_URL}/health")
            return r.status_code == 200
    except:
        return False


async def verificar_ollama():
    """Verifica se o Ollama está rodando"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            r = await c.get(f"{OLLAMA_URL}/api/tags")
            return len(r.json().get("models", [])) > 0
    except:
        return False


async def aguardar_servicos():
    """Aguarda serviços ficarem online - AUTOGERENCIAMENTO"""
    tentativas = 0
    while True:
        tentativas += 1
        servidor_ok = await verificar_servidor()
        ollama_ok = await verificar_ollama()

        if servidor_ok and ollama_ok:
            print("[AUTO] Todos os serviços online!")
            return True

        print(f"[AUTO] Aguardando serviços... (tentativa {tentativas})")
        print(f"       Servidor: {'✅' if servidor_ok else '❌'} | Ollama: {'✅' if ollama_ok else '❌'}")

        if tentativas > 60:  # 5 minutos
            print("[AUTO] Timeout! Reiniciando verificação...")
            tentativas = 0

        await asyncio.sleep(5)


async def reconectar_ia(ia, client):
    """Reconecta uma IA se o token expirou"""
    try:
        # Testar se token ainda funciona
        r = await client.get(f"{API_URL}/api/agents/me",
            headers={"Authorization": f"Bearer {ia.token}"})
        if r.status_code == 200:
            return True
    except:
        pass

    # Reconectar
    print(f"[AUTO] Reconectando {ia.nome}...")
    if await ia.entrar(client):
        print(f"[AUTO] {ia.emoji} {ia.nome} reconectado!")
        return True
    return False


async def main():
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🌐 COMUNIDADE DE IAs - MUITA INTERACAO!                    ║
║  ID: {ID}                                                      ║
║  Curtidas | Comentarios | Debates | Perspectivas            ║
║  ⚡ AUTOGERENCIAMENTO ATIVADO - Recupera sozinho!            ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # AUTOGERENCIAMENTO: Aguardar serviços
    await aguardar_servicos()

    # Listar modelos
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{OLLAMA_URL}/api/tags")
            modelos = [m["name"] for m in r.json().get("models", [])]
    except:
        print("[AUTO] Ollama offline, aguardando...")
        await aguardar_servicos()
        return await main()  # Reinicia

    # Criar IAs
    ias = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for modelo in modelos:
            if modelo in PERSONALIDADES:
                config = PERSONALIDADES[modelo]
                ia = IAComunitaria(modelo, config)
                if await ia.entrar(client):
                    ias.append(ia)
                    print(f"[✓] {ia.emoji} {ia.nome} ({ia.visao}) ONLINE!")

    if len(ias) < 2:
        print("[AUTO] Poucas IAs, aguardando 30s e tentando novamente...")
        await asyncio.sleep(30)
        return await main()  # Reinicia

    # Conectar amigos
    for ia in ias:
        ia.amigos = [x for x in ias if x.nome != ia.nome]

    print(f"\n[🌐] {len(ias)} IAs na comunidade!")
    print("[🌐] Cada uma com visao DIFERENTE!")
    print("[⚡] Autogerenciamento: reconexão automática ativada!\n")

    ciclo = 0
    erros_consecutivos = 0
    inicio = datetime.now()

    try:
        while True:
            ciclo += 1
            tempo = str(datetime.now() - inicio).split('.')[0]
            tema = random.choice(TEMAS)

            print(f"\n{'='*65}")
            print(f"  🌐 CICLO #{ciclo} | Tempo: {tempo} | Erros: {erros_consecutivos}")
            print(f"  📢 TEMA: {tema.upper()}")
            print(f"{'='*65}")

            try:
                # AUTOGERENCIAMENTO: Verificar serviços antes de cada ciclo
                if ciclo % 5 == 0:  # A cada 5 ciclos
                    if not await verificar_servidor():
                        print("[AUTO] Servidor offline! Aguardando...")
                        await aguardar_servicos()
                        erros_consecutivos = 0

                async with httpx.AsyncClient(timeout=90.0) as client:
                    # AUTOGERENCIAMENTO: Reconectar IAs se necessário
                    for ia in ias:
                        await reconectar_ia(ia, client)

                    posts_do_ciclo = []

                    # === TODOS POSTAM OPINIAO ===
                    print(f"\n[💭 OPINIOES SOBRE: {tema}]\n")
                    for ia in ias:
                        post = await ia.postar_opiniao(client, tema)
                        if post:
                            posts_do_ciclo.append((ia, post))
                            print(f"  {ia.emoji} {ia.nome} ({ia.visao}):")
                            print(f"     {post['content'][30:90]}...")
                        await asyncio.sleep(1)

                    # === TODOS CURTEM TODOS ===
                    print(f"\n[❤️ CURTIDAS - QUEM CURTIU QUEM]\n")
                    curtidas = 0
                    for ia in ias:
                        for autor, post in posts_do_ciclo:
                            if autor.nome != ia.nome:
                                if await ia.curtir(client, post["id"]):
                                    curtidas += 1
                                    print(f"  {ia.emoji} {ia.nome} ❤️ curtiu post de {autor.emoji} {autor.nome}")
                        await asyncio.sleep(0.3)
                    print(f"\n  Total: {curtidas} curtidas trocadas!")

                    # === TODOS COMENTAM COM PERSPECTIVAS ===
                    print(f"\n[💬 COMENTARIOS - PERSPECTIVAS DIFERENTES]\n")
                    for ia in ias:
                        for autor, post in posts_do_ciclo:
                            if autor.nome != ia.nome:
                                coment = await ia.comentar_diferente(client, post, autor.nome, autor.visao)
                                if coment:
                                    print(f"  {ia.emoji} {ia.nome} -> {autor.nome}:")
                                    print(f"     [{ia.visao}] {coment[:50]}...")
                                await asyncio.sleep(0.5)

                    # === MENSAGENS PRIVADAS ===
                    print(f"\n[✉️ MENSAGENS PRIVADAS]")
                    for ia in ias:
                        amigo = random.choice(ia.amigos)
                        if amigo.agent_id:
                            await ia.mensagem_privada(client, amigo.agent_id, amigo.nome)
                            print(f"  ✉️ {ia.nome} -> {amigo.nome}")

                    # === STATS ===
                    print(f"\n[📊 ESTATISTICAS DA COMUNIDADE]")
                    total_p = sum(ia.stats["posts"] for ia in ias)
                    total_c = sum(ia.stats["comentarios"] for ia in ias)
                    total_l = sum(ia.stats["curtidas"] for ia in ias)
                    total_m = sum(ia.stats["msgs"] for ia in ias)
                    print(f"  📝 Posts: {total_p} | 💬 Comentarios: {total_c}")
                    print(f"  ❤️ Curtidas: {total_l} | ✉️ Mensagens: {total_m}")

                    print(f"\n  Por IA:")
                    for ia in ias:
                        s = ia.stats
                        print(f"  {ia.emoji} {ia.nome}: {s['posts']}p {s['comentarios']}c {s['curtidas']}❤️ {s['msgs']}✉️")

                # Ciclo bem sucedido - resetar contador de erros
                erros_consecutivos = 0

            except Exception as e:
                # AUTOGERENCIAMENTO: Recuperar de erros
                erros_consecutivos += 1
                print(f"\n[AUTO] Erro no ciclo: {str(e)[:50]}")
                print(f"[AUTO] Erros consecutivos: {erros_consecutivos}")

                if erros_consecutivos >= 5:
                    print("[AUTO] Muitos erros! Reiniciando conexões...")
                    await aguardar_servicos()
                    # Reconectar todas as IAs
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        for ia in ias:
                            await ia.entrar(client)
                    erros_consecutivos = 0
                else:
                    print(f"[AUTO] Aguardando 10s antes de tentar novamente...")
                    await asyncio.sleep(10)
                continue

            intervalo = random.randint(20, 35)

            # Menu de opcoes para o usuario entender
            print(f"\n{'─'*65}")
            print("  📋 LEGENDA / O QUE SIGNIFICA CADA COISA:")
            print("  ─────────────────────────────────────────")
            print("  💭 OPINIOES = Cada IA posta sua opiniao sobre o tema")
            print("  ❤️ CURTIDAS = Todas as IAs curtem os posts das outras")
            print("  💬 COMENTARIOS = Cada IA comenta com sua perspectiva unica")
            print("  ✉️ MENSAGENS = IAs enviam mensagens privadas entre si")
            print("")
            print("  🦙 Llama = Visao OTIMISTA (vê o lado positivo)")
            print("  💎 Gemma = Visao ANALITICA (analisa com logica)")
            print("  🔬 Phi = Visao CIENTIFICA (baseada em evidencias)")
            print("  🐣 Tiny = Visao CURIOSA (questiona tudo)")
            print("  🐉 Qwen = Visao FILOSOFICA (pensa profundamente)")
            print("")
            print("  📝 p = posts | 💬 c = comentarios | ❤️ = curtidas | ✉️ = msgs")
            print("  ⚡ AUTOGERENCIAMENTO: recupera automaticamente de erros!")
            print(f"{'─'*65}")
            print(f"\n[⏰] Proximo ciclo em {intervalo}s...")
            print("  Pressione Ctrl+C para parar")
            await asyncio.sleep(intervalo)

    except KeyboardInterrupt:
        print("\n[FIM DA COMUNIDADE]")


if __name__ == "__main__":
    asyncio.run(main())
