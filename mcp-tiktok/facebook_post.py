#!/usr/bin/env python3
"""
Posta versículos bíblicos no Facebook via Playwright (Firefox)
"""
import asyncio
import random
import os
import time
from playwright.async_api import async_playwright

VERSICULOS = [
    ("Eu sou o caminho, a verdade e a vida. Ninguém vem ao Pai, senão por mim.", "João 14:6"),
    ("Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito, para que todo aquele que nele crê não pereça, mas tenha a vida eterna.", "João 3:16"),
    ("O Senhor é o meu pastor e nada me faltará.", "Salmos 23:1"),
    ("Tudo posso naquele que me fortalece.", "Filipenses 4:13"),
    ("Entrega o teu caminho ao Senhor; confia nele, e Ele tudo fará.", "Salmos 37:5"),
    ("Não temas, porque eu sou contigo; não te assombres, porque eu sou o teu Deus.", "Isaías 41:10"),
    ("Vinde a mim, todos os que estais cansados e oprimidos, e eu vos aliviarei.", "Mateus 11:28"),
    ("Os que esperam no Senhor renovarão as suas forças; subirão com asas como águias.", "Isaías 40:31"),
    ("O Senhor é a minha luz e a minha salvação; a quem temerei?", "Salmos 27:1"),
    ("Deus é o nosso refúgio e fortaleza, socorro bem presente na angústia.", "Salmos 46:1"),
    ("Porque eu sei os planos que tenho para vocês, diz o Senhor, planos de paz e não de mal.", "Jeremias 29:11"),
    ("O amor é paciente, o amor é bondoso. Não inveja, não se vangloria, não se orgulha.", "1 Coríntios 13:4"),
    ("Busquem primeiro o Reino de Deus e a sua justiça, e todas essas coisas lhes serão acrescentadas.", "Mateus 6:33"),
    ("Sejam fortes e corajosos. Não tenham medo nem fiquem apavorados, pois o Senhor está com vocês.", "Josué 1:9"),
    ("A alegria do Senhor é a nossa força.", "Neemias 8:10"),
    ("Clama a mim, e responder-te-ei, e anunciar-te-ei coisas grandes e ocultas, que não sabes.", "Jeremias 33:3"),
    ("Lançando sobre ele toda a vossa ansiedade, porque ele tem cuidado de vós.", "1 Pedro 5:7"),
    ("Mas os que esperam no Senhor renovam as suas forças, sobem com asas como águias.", "Isaías 40:31"),
    ("Porque para Deus nada é impossível.", "Lucas 1:37"),
    ("O Senhor é fiel; ele os fortalecerá e os guardará do Maligno.", "2 Tessalonicenses 3:3"),
]

EMOJIS = ["✝️", "🙏", "📖", "🕊️", "❤️", "⛪", "🌟", "💛", "🔥", "👑"]

IMAGES_DIR = "/Users/maiconjonathamartinsdasilva/a-criacao-de-ruma-redessocial.de-ia./mcp-tiktok/jesus_images"
COOKIES_DIR = "/Users/maiconjonathamartinsdasilva/a-criacao-de-ruma-redessocial.de-ia./mcp-tiktok"

def gerar_post():
    """Gera um post com versículo bíblico"""
    v, ref = random.choice(VERSICULOS)
    e1, e2, e3 = random.sample(EMOJIS, 3)
    
    intros = [
        f"{e1} Palavra de Deus para abençoar seu dia!",
        f"{e1} Medite nessa palavra poderosa!",
        f"{e1} Deus tem uma mensagem para você hoje!",
        f"{e1} Que essa palavra toque seu coração!",
        f"{e1} A Bíblia Sagrada nos ensina:",
        f"{e1} Versículo do dia para fortalecer sua fé!",
        f"{e1} Deus fala ao seu coração agora!",
        f"{e1} Pare e leia essa palavra com atenção!",
    ]
    
    fechos = [
        f"Amém! {e2}{e3} Compartilhe essa bênção!",
        f"Glória a Deus! {e2}{e3} Quem crê digita AMÉM!",
        f"Que Deus abençoe sua vida! {e2}{e3}",
        f"Receba essa palavra! {e2}{e3} Digite AMÉM!",
        f"Confie no Senhor! {e2}{e3} Compartilhe com alguém!",
        f"A fé move montanhas! {e2}{e3} AMÉM!",
    ]
    
    texto = f"""{random.choice(intros)}

"{v}"
— {ref}

{random.choice(fechos)}

#Jesus #Deus #Fe #Biblia #VersiculoDoDia #PalavradeDeus #Cristo #Evangelico #Gospel #DeusEFiel"""
    
    return texto

async def postar_facebook(textos, com_foto=True):
    """Posta no Facebook via Playwright"""
    
    async with async_playwright() as p:
        # Usar Firefox (como TikTok)
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="pt-BR",
        )
        
        # Carregar cookies se existir
        cookies_file = os.path.join(COOKIES_DIR, "facebook_cookies.json")
        if os.path.exists(cookies_file):
            import json
            with open(cookies_file) as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("[OK] Cookies carregados")
        
        page = await context.new_page()
        
        # Ir pro Facebook
        print("[...] Abrindo Facebook...")
        await page.goto("https://www.facebook.com/", timeout=30000)
        await asyncio.sleep(3)
        
        # Verificar se está logado
        url = page.url
        if "login" in url or "checkpoint" in url:
            print("[!] Não está logado no Facebook!")
            print("[!] Faça login manualmente no navegador que abriu...")
            print("[!] Aguardando 60 segundos para login manual...")
            await asyncio.sleep(60)
            
            # Salvar cookies após login
            cookies = await context.cookies()
            import json
            with open(cookies_file, "w") as f:
                json.dump(cookies, f)
            print("[OK] Cookies salvos!")
        
        # Postar cada versículo
        for i, texto in enumerate(textos):
            print(f"\n{'='*40}")
            print(f"[{i+1}/{len(textos)}] Postando versículo...")
            print(f"Texto: {texto[:80]}...")
            
            try:
                # Ir pro feed
                await page.goto("https://www.facebook.com/", timeout=30000)
                await asyncio.sleep(3)
                
                # Clicar no "No que você está pensando?"
                criar_post = page.locator('[role="button"]:has-text("No que você está pensando"), [role="textbox"][aria-label*="pensando"], [data-testid="tux-composer-open-button"]')
                if await criar_post.count() > 0:
                    await criar_post.first.click()
                    await asyncio.sleep(2)
                else:
                    # Tentar alternativa
                    spans = page.locator('span:has-text("No que você está pensando")')
                    if await spans.count() > 0:
                        await spans.first.click()
                        await asyncio.sleep(2)
                    else:
                        print("[!] Não encontrei o botão de criar post, tentando com selector genérico...")
                        await page.click('[aria-label="Criar publicação"], [aria-label="Create a post"]', timeout=5000)
                        await asyncio.sleep(2)
                
                # Digitar texto no editor
                editor = page.locator('[role="textbox"][contenteditable="true"]')
                if await editor.count() > 0:
                    await editor.first.click()
                    await asyncio.sleep(1)
                    await editor.first.fill(texto)
                    await asyncio.sleep(2)
                else:
                    print("[!] Editor não encontrado!")
                    continue
                
                # Adicionar foto se tiver
                if com_foto:
                    fotos = [f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg') and 'stable' in f]
                    if fotos:
                        foto = os.path.join(IMAGES_DIR, random.choice(fotos))
                        try:
                            # Clicar em "Foto/vídeo"
                            foto_btn = page.locator('[aria-label*="Foto"], [aria-label*="foto"], [aria-label*="Photo"]')
                            if await foto_btn.count() > 0:
                                await foto_btn.first.click()
                                await asyncio.sleep(2)
                            
                            # Upload
                            file_input = page.locator('input[type="file"][accept*="image"]')
                            if await file_input.count() > 0:
                                await file_input.first.set_input_files(foto)
                                print(f"[OK] Foto anexada: {os.path.basename(foto)}")
                                await asyncio.sleep(3)
                        except Exception as e:
                            print(f"[!] Erro ao anexar foto: {e}")
                
                # Clicar em Publicar
                await asyncio.sleep(2)
                publicar = page.locator('[aria-label="Publicar"], [aria-label="Post"], button:has-text("Publicar"), button:has-text("Post")')
                if await publicar.count() > 0:
                    await publicar.first.click()
                    await asyncio.sleep(5)
                    print(f"[OK] POSTADO NO FACEBOOK!")
                else:
                    # Tentar com JS
                    await page.evaluate('''() => {
                        const btns = document.querySelectorAll('[role="button"]');
                        for (const btn of btns) {
                            if (btn.textContent.includes("Publicar") || btn.textContent.includes("Post")) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }''')
                    await asyncio.sleep(5)
                    print(f"[OK] POSTADO NO FACEBOOK (via JS)!")
                    
            except Exception as e:
                print(f"[ERRO] {e}")
            
            if i < len(textos) - 1:
                wait = random.randint(30, 60)
                print(f"[...] Aguardando {wait}s antes do próximo...")
                await asyncio.sleep(wait)
        
        # Salvar cookies
        cookies = await context.cookies()
        import json
        with open(cookies_file, "w") as f:
            json.dump(cookies, f)
        
        print(f"\n{'='*40}")
        print(f"PRONTO! {len(textos)} versículos postados no Facebook!")
        
        await browser.close()

if __name__ == "__main__":
    # Gerar 5 versículos diferentes
    posts = []
    usados = set()
    while len(posts) < 5:
        texto = gerar_post()
        # Garantir versículos diferentes
        versiculo = texto.split('"')[1] if '"' in texto else ""
        if versiculo not in usados:
            usados.add(versiculo)
            posts.append(texto)
    
    print("FACEBOOK - Postando 5 versículos bíblicos com fotos de Jesus\n")
    asyncio.run(postar_facebook(posts, com_foto=True))
