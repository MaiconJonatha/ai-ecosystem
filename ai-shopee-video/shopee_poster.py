#!/usr/bin/env python3
"""
Shopee Automation - Login + Criação de Produtos + Upload de Vídeos
Usa Playwright (Firefox) para automatizar o Shopee Seller Center
"""
import asyncio
import json
import os
import random
import time
import glob
import argparse
from datetime import datetime
from playwright.async_api import async_playwright

DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_FILE = os.path.join(DIR, "shopee_cookies.json")
VIDEOS_DIR = os.path.join(DIR, "static", "videos")
IMAGES_DIR = os.path.join(DIR, "static", "images")
ACCOUNTS_FILE = os.path.join(DIR, "shopee_accounts.json")
LOG_FILE = os.path.join(DIR, "shopee_automation.log")

# Shopee Seller Center URLs
SHOPEE_SELLER = "https://seller.shopee.com.br"
SHOPEE_LOGIN = "https://seller.shopee.com.br/account/signin"
SHOPEE_ADD_PRODUCT = "https://seller.shopee.com.br/portal/product/new"
SHOPEE_VIDEO = "https://seller.shopee.com.br/portal/media-center"

# Categorias Shopee Brasil (IDs reais do sistema)
CATEGORIAS_MAP = {
    "cozinha": "Casa & Cozinha",
    "pets": "Animais de Estimação",
    "iluminacao": "Casa & Decoração",
    "gadgets": "Celulares & Telecomunicações",
    "beleza": "Beleza",
    "casa": "Casa & Organização",
}


def log(msg):
    """Log com timestamp"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def get_videos():
    """Lista vídeos gerados disponíveis para postar"""
    videos = glob.glob(os.path.join(VIDEOS_DIR, "shopee_*.mp4"))
    return sorted(videos, key=os.path.getmtime, reverse=True)


def get_product_images():
    """Lista imagens de produtos disponíveis"""
    imgs = glob.glob(os.path.join(IMAGES_DIR, "prod_*.*"))
    return sorted(imgs, key=os.path.getmtime, reverse=True)


def load_posted():
    """Carrega lista de vídeos já postados"""
    posted_file = os.path.join(DIR, "shopee_posted.json")
    if os.path.exists(posted_file):
        with open(posted_file) as f:
            return json.load(f)
    return []


def save_posted(posted):
    """Salva lista de vídeos já postados"""
    posted_file = os.path.join(DIR, "shopee_posted.json")
    with open(posted_file, "w") as f:
        json.dump(posted, f, indent=2)


async def shopee_login(headless=False):
    """
    Login no Shopee Seller Center.
    Usa Chromium com channel=chrome para parecer Chrome real.
    """
    log("[LOGIN] Iniciando login no Shopee Seller Center (Chrome)...")

    async with async_playwright() as p:
        # Usar Chromium com channel chrome para evitar detecção
        browser = await p.chromium.launch(
            headless=headless,
            channel="chrome",  # Usa o Chrome real instalado
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )

        # Remover navigator.webdriver para evitar detecção
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)

        # Carregar cookies existentes se houver
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE) as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            log("[LOGIN] Cookies carregados, verificando sessão...")

        page = await context.new_page()

        # Ir pro Seller Center
        await page.goto(SHOPEE_SELLER, timeout=30000)
        await asyncio.sleep(3)

        url = page.url
        if "signin" in url or "login" in url:
            log("[LOGIN] Não está logado. Faça login manualmente no Chrome...")
            log("[LOGIN] Aguardando até 180 segundos para login...")

            # Aguardar redirecionamento após login
            for i in range(90):
                await asyncio.sleep(2)
                url = page.url
                if "signin" not in url and "login" not in url:
                    log(f"[LOGIN] Login detectado! URL: {url}")
                    break
                if i % 15 == 0 and i > 0:
                    log(f"[LOGIN] Aguardando login... {i*2}s")

            if "signin" in page.url or "login" in page.url:
                log("[LOGIN] Timeout! Não foi possível detectar login.")
                await browser.close()
                return False

        # Salvar cookies
        cookies = await context.cookies()
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f)
        log(f"[LOGIN] Cookies salvos! ({len(cookies)} cookies)")

        # Salvar info da conta
        title = await page.title()
        log(f"[LOGIN] Logado: {title}")

        await browser.close()
        return True


async def shopee_post_product(video_path, product_info=None, headless=False):
    """
    Cria um novo produto no Shopee Seller Center com vídeo.

    Args:
        video_path: Caminho do vídeo MP4
        product_info: Dict com {nome, descricao, preco, categoria, imagem}
        headless: Executar sem janela
    """
    if not os.path.exists(video_path):
        log(f"[ERRO] Vídeo não encontrado: {video_path}")
        return False

    if not os.path.exists(COOKIES_FILE):
        log("[ERRO] Sem cookies! Faça login primeiro: python shopee_poster.py --login")
        return False

    # Info padrão do produto se não fornecida
    if not product_info:
        product_info = _generate_product_info()

    log(f"[POST] Postando produto: {product_info['nome'][:50]}...")
    log(f"[POST] Vídeo: {os.path.basename(video_path)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        # Carregar cookies
        with open(COOKIES_FILE) as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

        page = await context.new_page()

        try:
            # 1. Ir para página de adicionar produto
            log("[POST] Abrindo página de novo produto...")
            await page.goto(SHOPEE_ADD_PRODUCT, timeout=30000)
            await asyncio.sleep(3)

            # Verificar se está logado
            if "signin" in page.url or "login" in page.url:
                log("[POST] Sessão expirada! Faça login novamente.")
                await browser.close()
                return False

            log(f"[POST] Página carregada: {await page.title()}")

            # 2. Preencher nome do produto
            await _fill_product_name(page, product_info["nome"])

            # 3. Preencher descrição
            await _fill_product_description(page, product_info["descricao"])

            # 4. Upload de imagem principal
            if product_info.get("imagem") and os.path.exists(product_info["imagem"]):
                await _upload_product_image(page, product_info["imagem"])

            # 5. Upload de vídeo
            await _upload_product_video(page, video_path)

            # 6. Definir preço
            await _set_product_price(page, product_info["preco"])

            # 7. Definir estoque
            await _set_product_stock(page, product_info.get("estoque", 999))

            # 8. Selecionar categoria
            await _select_category(page, product_info.get("categoria_nome", ""))

            # 9. Publicar
            success = await _publish_product(page)

            if success:
                log(f"[POST] PRODUTO PUBLICADO: {product_info['nome'][:50]}")
                # Salvar cookies atualizados
                new_cookies = await context.cookies()
                with open(COOKIES_FILE, "w") as f:
                    json.dump(new_cookies, f)
            else:
                log("[POST] Falha ao publicar. Salvando screenshot...")
                await page.screenshot(path=os.path.join(DIR, "shopee_error.png"))

            await browser.close()
            return success

        except Exception as e:
            log(f"[ERRO] {e}")
            try:
                await page.screenshot(path=os.path.join(DIR, "shopee_error.png"))
            except:
                pass
            await browser.close()
            return False


async def _fill_product_name(page, nome):
    """Preenche o nome do produto"""
    try:
        # Shopee Seller Center usa inputs com placeholders
        name_input = page.locator('input[placeholder*="nome"], input[placeholder*="Nome"], input[placeholder*="product name"], .product-edit-form-item input').first
        await name_input.click()
        await asyncio.sleep(0.5)
        await name_input.fill(nome[:120])  # Limite de 120 chars
        log(f"[POST] Nome preenchido: {nome[:50]}...")
        await asyncio.sleep(1)
    except Exception as e:
        log(f"[POST] Erro ao preencher nome: {e}")
        # Fallback: tentar via JS
        await page.evaluate(f'''() => {{
            const inputs = document.querySelectorAll('input[type="text"]');
            for (const inp of inputs) {{
                if (inp.placeholder && (inp.placeholder.includes("nome") || inp.placeholder.includes("Nome") || inp.placeholder.includes("product"))) {{
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(inp, {json.dumps(nome[:120])});
                    inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }}
            }}
            return false;
        }}''')


async def _fill_product_description(page, descricao):
    """Preenche a descrição do produto"""
    try:
        # Editor de descrição (pode ser contenteditable ou textarea)
        desc_editor = page.locator('[contenteditable="true"], textarea[placeholder*="descri"], textarea[placeholder*="Descri"]').first
        await desc_editor.click()
        await asyncio.sleep(0.5)
        await desc_editor.fill(descricao[:3000])
        log("[POST] Descrição preenchida")
        await asyncio.sleep(1)
    except Exception as e:
        log(f"[POST] Erro ao preencher descrição: {e}")


async def _upload_product_image(page, img_path):
    """Faz upload da imagem principal do produto"""
    try:
        file_input = page.locator('input[type="file"][accept*="image"]').first
        await file_input.set_input_files(img_path)
        log(f"[POST] Imagem uploaded: {os.path.basename(img_path)}")
        await asyncio.sleep(3)  # Esperar upload
    except Exception as e:
        log(f"[POST] Erro upload imagem: {e}")


async def _upload_product_video(page, video_path):
    """Faz upload do vídeo do produto"""
    try:
        # Procurar input de vídeo
        file_inputs = page.locator('input[type="file"]')
        count = await file_inputs.count()

        for i in range(count):
            accept = await file_inputs.nth(i).get_attribute("accept") or ""
            if "video" in accept or "mp4" in accept:
                await file_inputs.nth(i).set_input_files(video_path)
                log(f"[POST] Vídeo uploaded: {os.path.basename(video_path)}")
                await asyncio.sleep(5)  # Vídeos demoram mais
                return

        # Fallback: tentar qualquer file input que aceite vídeo
        for i in range(count):
            try:
                await file_inputs.nth(i).set_input_files(video_path)
                log(f"[POST] Vídeo uploaded (fallback input {i})")
                await asyncio.sleep(5)
                return
            except:
                continue

        log("[POST] Nenhum input de vídeo encontrado")
    except Exception as e:
        log(f"[POST] Erro upload vídeo: {e}")


async def _set_product_price(page, preco):
    """Define o preço do produto"""
    try:
        # Limpar e converter preço
        preco_str = str(preco).replace("R$", "").replace(" ", "").replace(",", ".").strip()

        price_input = page.locator('input[placeholder*="preço"], input[placeholder*="Preço"], input[placeholder*="price"], input[name*="price"]').first
        await price_input.click()
        await asyncio.sleep(0.3)
        await price_input.fill(preco_str)
        log(f"[POST] Preço definido: R$ {preco_str}")
        await asyncio.sleep(0.5)
    except Exception as e:
        log(f"[POST] Erro ao definir preço: {e}")


async def _set_product_stock(page, estoque):
    """Define o estoque"""
    try:
        stock_input = page.locator('input[placeholder*="estoq"], input[placeholder*="Estoq"], input[placeholder*="stock"], input[name*="stock"]').first
        await stock_input.click()
        await asyncio.sleep(0.3)
        await stock_input.fill(str(estoque))
        log(f"[POST] Estoque: {estoque}")
        await asyncio.sleep(0.5)
    except Exception as e:
        log(f"[POST] Erro ao definir estoque: {e}")


async def _select_category(page, categoria_nome):
    """Seleciona a categoria do produto"""
    try:
        # Clicar no seletor de categoria
        cat_btn = page.locator('button:has-text("categoria"), button:has-text("Categoria"), [class*="category"] button, .product-category').first
        await cat_btn.click()
        await asyncio.sleep(2)

        # Buscar a categoria
        if categoria_nome:
            search = page.locator('input[placeholder*="Buscar"], input[placeholder*="buscar"], input[placeholder*="search"]').first
            await search.fill(categoria_nome)
            await asyncio.sleep(1)

            # Clicar no primeiro resultado
            result = page.locator(f'text="{categoria_nome}"').first
            await result.click()
            await asyncio.sleep(1)

        log(f"[POST] Categoria: {categoria_nome}")
    except Exception as e:
        log(f"[POST] Erro categoria: {e} (pode precisar selecionar manualmente)")


async def _publish_product(page):
    """Clica no botão de publicar"""
    try:
        await asyncio.sleep(2)

        # Procurar botão de publicar/salvar
        selectors = [
            'button:has-text("Publicar")',
            'button:has-text("Salvar e Publicar")',
            'button:has-text("Save and Publish")',
            'button:has-text("Publish")',
            'button:has-text("Salvar")',
            '[class*="submit"] button',
        ]

        for sel in selectors:
            btn = page.locator(sel)
            if await btn.count() > 0:
                await btn.first.click()
                log("[POST] Botão de publicar clicado!")
                await asyncio.sleep(5)
                return True

        # Fallback: JS
        result = await page.evaluate('''() => {
            const btns = document.querySelectorAll('button');
            for (const btn of btns) {
                const text = btn.textContent.toLowerCase();
                if (text.includes("publicar") || text.includes("publish") || text.includes("salvar")) {
                    btn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                    return btn.textContent;
                }
            }
            return null;
        }''')

        if result:
            log(f"[POST] Publicado via JS: {result}")
            await asyncio.sleep(5)
            return True

        log("[POST] Botão de publicar não encontrado!")
        return False

    except Exception as e:
        log(f"[POST] Erro ao publicar: {e}")
        return False


async def shopee_upload_video_media_center(video_path, headless=False):
    """
    Upload de vídeo direto no Media Center da Shopee (Shopee Video/Feed).
    Diferente de produto - é só vídeo de conteúdo estilo TikTok/Reels.
    """
    if not os.path.exists(COOKIES_FILE):
        log("[ERRO] Sem cookies! Faça login primeiro.")
        return False

    log(f"[VIDEO] Upload para Shopee Video: {os.path.basename(video_path)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        with open(COOKIES_FILE) as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

        page = await context.new_page()

        try:
            # Ir para o Media Center
            await page.goto(SHOPEE_VIDEO, timeout=30000)
            await asyncio.sleep(3)

            if "signin" in page.url:
                log("[VIDEO] Sessão expirada!")
                await browser.close()
                return False

            # Procurar botão de upload/criar vídeo
            upload_btn = page.locator('button:has-text("Upload"), button:has-text("Criar"), button:has-text("Novo"), [class*="upload"]').first
            if await upload_btn.count() > 0:
                await upload_btn.click()
                await asyncio.sleep(2)

            # Upload do arquivo
            file_input = page.locator('input[type="file"]').first
            await file_input.set_input_files(video_path)
            log("[VIDEO] Arquivo enviado, aguardando processamento...")
            await asyncio.sleep(10)  # Shopee processa vídeo

            # Publicar
            pub_btn = page.locator('button:has-text("Publicar"), button:has-text("Postar"), button:has-text("Publish")').first
            if await pub_btn.count() > 0:
                await pub_btn.click()
                await asyncio.sleep(5)
                log("[VIDEO] Vídeo publicado no Shopee Video!")
                await browser.close()
                return True

            log("[VIDEO] Botão de publicar não encontrado")
            await page.screenshot(path=os.path.join(DIR, "shopee_video_error.png"))
            await browser.close()
            return False

        except Exception as e:
            log(f"[VIDEO] Erro: {e}")
            await browser.close()
            return False


def _generate_product_info():
    """Gera informações de produto baseado nos vídeos disponíveis"""
    from app.main import CATEGORIAS_SHOPEE, FRASES_ABERTURA, FRASES_CTA

    cat_key = random.choice(list(CATEGORIAS_SHOPEE.keys()))
    cat = CATEGORIAS_SHOPEE[cat_key]
    produto = random.choice(cat["produtos"])

    preco = f"{random.randint(19, 149)}.{random.choice(['90', '99'])}"

    return {
        "nome": f"{produto.title()} - {random.choice(FRASES_ABERTURA)[:20]} - Frete Grátis",
        "descricao": f"""🔥 {produto.title()} - O MELHOR DA SHOPEE!

✅ Qualidade premium garantida
✅ Entrega rápida para todo Brasil
✅ Frete grátis
✅ Garantia de satisfação

📦 Envio imediato após confirmação do pagamento
⭐ Avaliação 5 estrelas pelos compradores

{cat['hashtags']}

💰 APROVEITE! Preço promocional por tempo limitado!
🛒 Adicione ao carrinho antes que acabe!""",
        "preco": preco,
        "estoque": 999,
        "categoria": cat_key,
        "categoria_nome": CATEGORIAS_MAP.get(cat_key, "Outros"),
        "imagem": "",
    }


async def auto_post_loop(max_posts=10, intervalo=120, headless=False):
    """
    Loop automático que posta vídeos na Shopee.

    Args:
        max_posts: Número máximo de posts
        intervalo: Segundos entre posts
        headless: Executar sem janela
    """
    posted = load_posted()
    posted_set = set(posted)
    videos = get_videos()
    images = get_product_images()

    available = [v for v in videos if v not in posted_set]

    if not available:
        log("[AUTO] Nenhum vídeo novo disponível para postar!")
        return

    log(f"[AUTO] Iniciando loop: {len(available)} vídeos disponíveis, max {max_posts} posts")

    count = 0
    for video_path in available[:max_posts]:
        count += 1
        log(f"\n{'='*50}")
        log(f"[AUTO] Post {count}/{min(max_posts, len(available))}")

        # Gerar info do produto
        product_info = _generate_product_info()

        # Associar imagem se tiver
        if images:
            product_info["imagem"] = random.choice(images[:20])  # Imagens mais recentes

        # Tentar postar como produto
        success = await shopee_post_product(video_path, product_info, headless=headless)

        if success:
            posted.append(video_path)
            save_posted(posted)
            log(f"[AUTO] Post #{count} OK: {product_info['nome'][:50]}")
        else:
            log(f"[AUTO] Post #{count} FALHOU")
            # Tentar só como vídeo no Media Center
            log("[AUTO] Tentando upload direto no Shopee Video...")
            success2 = await shopee_upload_video_media_center(video_path, headless=headless)
            if success2:
                posted.append(video_path)
                save_posted(posted)

        if count < min(max_posts, len(available)):
            wait = intervalo + random.randint(-30, 30)
            log(f"[AUTO] Próximo post em {wait}s...")
            await asyncio.sleep(wait)

    log(f"\n{'='*50}")
    log(f"[AUTO] Concluído! {count} posts tentados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shopee Automation - Criar produtos e postar vídeos")
    parser.add_argument("--login", action="store_true", help="Fazer login no Shopee Seller Center")
    parser.add_argument("--post", type=str, help="Postar um vídeo específico (caminho do .mp4)")
    parser.add_argument("--video", type=str, help="Upload vídeo no Shopee Video/Feed")
    parser.add_argument("--auto", action="store_true", help="Loop automático de posts")
    parser.add_argument("--max", type=int, default=10, help="Máximo de posts no modo auto (default: 10)")
    parser.add_argument("--intervalo", type=int, default=120, help="Segundos entre posts (default: 120)")
    parser.add_argument("--headless", action="store_true", help="Executar sem janela")
    parser.add_argument("--listar", action="store_true", help="Listar vídeos disponíveis")

    args = parser.parse_args()

    if args.login:
        asyncio.run(shopee_login(headless=False))  # Login sempre com janela

    elif args.post:
        asyncio.run(shopee_post_product(args.post, headless=args.headless))

    elif args.video:
        asyncio.run(shopee_upload_video_media_center(args.video, headless=args.headless))

    elif args.auto:
        asyncio.run(auto_post_loop(
            max_posts=args.max,
            intervalo=args.intervalo,
            headless=args.headless,
        ))

    elif args.listar:
        videos = get_videos()
        posted = set(load_posted())
        print(f"\n📹 Vídeos disponíveis: {len(videos)}")
        print(f"✅ Já postados: {len(posted)}")
        print(f"🆕 Novos: {len([v for v in videos if v not in posted])}")
        print()
        for v in videos[:20]:
            status = "✅" if v in posted else "🆕"
            size = os.path.getsize(v) // 1024
            print(f"  {status} {os.path.basename(v)} ({size}KB)")
        if len(videos) > 20:
            print(f"  ... e mais {len(videos) - 20} vídeos")

    else:
        parser.print_help()
        print("\n📋 Exemplos:")
        print("  python shopee_poster.py --login                  # Login no Shopee")
        print("  python shopee_poster.py --listar                 # Ver vídeos disponíveis")
        print("  python shopee_poster.py --post video.mp4         # Postar 1 produto")
        print("  python shopee_poster.py --video video.mp4        # Upload no Shopee Video")
        print("  python shopee_poster.py --auto --max 5           # Auto-post 5 produtos")
        print("  python shopee_poster.py --auto --max 10 --intervalo 180  # 10 posts, 3min entre cada")
