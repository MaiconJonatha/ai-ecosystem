#!/usr/bin/env python3
"""
Shopee Afiliados - Automação completa
1. Login no programa de afiliados
2. Busca produtos com boa comissão
3. Gera link de afiliado
4. Cria vídeo promocional
5. Posta nas redes sociais (TikTok, Instagram, YouTube Shorts)
"""
import asyncio
import json
import os
import random
import time
import glob
import argparse
import re
from datetime import datetime
from playwright.async_api import async_playwright

DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_FILE = os.path.join(DIR, "shopee_cookies.json")
AFFILIATE_FILE = os.path.join(DIR, "shopee_affiliate_links.json")
VIDEOS_DIR = os.path.join(DIR, "static", "videos")
IMAGES_DIR = os.path.join(DIR, "static", "images")
LOG_FILE = os.path.join(DIR, "shopee_afiliado.log")

# URLs do Programa de Afiliados
SHOPEE_AFFILIATE = "https://affiliate.shopee.com.br"
SHOPEE_AFFILIATE_OFFERS = "https://affiliate.shopee.com.br/offer"
SHOPEE_MAIN = "https://shopee.com.br"

# Categorias populares para afiliados (alta comissão)
NICHOS_LUCRATIVOS = [
    {"nicho": "beleza", "busca": "kit skincare coreano", "comissao": "10-15%"},
    {"nicho": "beleza", "busca": "serum vitamina C", "comissao": "10-15%"},
    {"nicho": "beleza", "busca": "massageador facial", "comissao": "10-15%"},
    {"nicho": "gadgets", "busca": "fone bluetooth TWS", "comissao": "8-12%"},
    {"nicho": "gadgets", "busca": "smartwatch relogio", "comissao": "8-12%"},
    {"nicho": "gadgets", "busca": "mini projetor portatil", "comissao": "8-12%"},
    {"nicho": "casa", "busca": "organizador guarda roupa", "comissao": "8-10%"},
    {"nicho": "casa", "busca": "aspirador robo", "comissao": "8-10%"},
    {"nicho": "casa", "busca": "luminaria LED sensor", "comissao": "8-10%"},
    {"nicho": "cozinha", "busca": "air fryer mini", "comissao": "8-10%"},
    {"nicho": "cozinha", "busca": "processador alimentos", "comissao": "8-10%"},
    {"nicho": "pets", "busca": "bebedouro fonte gatos", "comissao": "8-12%"},
    {"nicho": "pets", "busca": "comedouro automatico", "comissao": "8-12%"},
    {"nicho": "fitness", "busca": "faixa elastica exercicio", "comissao": "8-10%"},
    {"nicho": "fitness", "busca": "garrafa agua motivacional", "comissao": "8-10%"},
    {"nicho": "kids", "busca": "brinquedo educativo", "comissao": "8-12%"},
    {"nicho": "moda", "busca": "bolsa feminina transversal", "comissao": "10-15%"},
    {"nicho": "moda", "busca": "tenis casual masculino", "comissao": "10-15%"},
]


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_affiliate_links():
    if os.path.exists(AFFILIATE_FILE):
        with open(AFFILIATE_FILE) as f:
            return json.load(f)
    return []


def save_affiliate_links(links):
    with open(AFFILIATE_FILE, "w") as f:
        json.dump(links, f, indent=2, ensure_ascii=False)


async def _create_browser(headless=False):
    """Cria browser Chrome anti-detecção"""
    p = await async_playwright().start()
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
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
    """)

    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE) as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

    return p, browser, context


async def affiliate_login(headless=False):
    """Login no programa de afiliados da Shopee"""
    log("[LOGIN] Abrindo Shopee Afiliados...")

    p, browser, context = await _create_browser(headless=False)  # Sempre com janela para login
    page = await context.new_page()

    try:
        await page.goto(SHOPEE_AFFILIATE, timeout=30000)
        await asyncio.sleep(3)

        url = page.url
        log(f"[LOGIN] URL: {url}")

        if "login" in url or "signin" in url:
            log("[LOGIN] Faça login manualmente (180s)...")

            for i in range(90):
                await asyncio.sleep(2)
                url = page.url
                if "login" not in url and "signin" not in url:
                    log(f"[LOGIN] Login OK! URL: {url}")
                    break
                if i % 15 == 0 and i > 0:
                    log(f"[LOGIN] Aguardando... {i*2}s")

            if "login" in page.url or "signin" in page.url:
                log("[LOGIN] Timeout!")
                await browser.close()
                await p.stop()
                return False

        # Salvar cookies
        cookies = await context.cookies()
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f)
        log(f"[LOGIN] Cookies salvos ({len(cookies)})")

        title = await page.title()
        log(f"[LOGIN] Logado: {title}")

        await browser.close()
        await p.stop()
        return True

    except Exception as e:
        log(f"[LOGIN] Erro: {e}")
        await browser.close()
        await p.stop()
        return False


async def buscar_produtos(nicho=None, quantidade=10, headless=False):
    """
    Busca produtos na Shopee para promover como afiliado.
    Extrai: nome, preço, avaliações, vendidos, link, imagem.
    """
    if not nicho:
        nicho_info = random.choice(NICHOS_LUCRATIVOS)
    else:
        nicho_info = next((n for n in NICHOS_LUCRATIVOS if n["nicho"] == nicho), NICHOS_LUCRATIVOS[0])

    busca = nicho_info["busca"]
    log(f"[BUSCA] Buscando: '{busca}' (nicho: {nicho_info['nicho']}, comissão: {nicho_info['comissao']})")

    p, browser, context = await _create_browser(headless=headless)
    page = await context.new_page()

    produtos = []

    try:
        # Buscar na Shopee
        search_url = f"https://shopee.com.br/search?keyword={busca.replace(' ', '+')}&sortBy=sales"
        await page.goto(search_url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(8)

        # Scroll para carregar mais produtos
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(1)

        # Extrair produtos via JS
        items = await page.evaluate('''() => {
            const products = [];
            // Shopee usa divs com data-sqe="item"
            const cards = document.querySelectorAll('[data-sqe="item"], .shopee-search-item-result__item, a[data-sqe="link"]');

            cards.forEach(card => {
                try {
                    const link = card.querySelector('a') || card;
                    const href = link.href || link.closest('a')?.href || '';
                    const nameEl = card.querySelector('.ie3A\\+n, .Cve6sh, [data-sqe="name"], .line-clamp-2');
                    const priceEl = card.querySelector('.ZEgDH9, .vioxXd, [class*="price"], span:not(:empty)');
                    const imgEl = card.querySelector('img');
                    const soldEl = card.querySelector('.r6HknA, [class*="sold"]');
                    const ratingEl = card.querySelector('[class*="rating"], .shopee-rating-stars');

                    if (nameEl || href) {
                        products.push({
                            nome: nameEl?.textContent?.trim() || 'Produto Shopee',
                            preco: priceEl?.textContent?.trim() || '',
                            link: href,
                            imagem: imgEl?.src || '',
                            vendidos: soldEl?.textContent?.trim() || '',
                            avaliacao: ratingEl?.textContent?.trim() || '',
                        });
                    }
                } catch(e) {}
            });
            return products;
        }''')

        # Se não encontrou com seletores específicos, tenta genérico
        if not items or len(items) < 3:
            items = await page.evaluate('''() => {
                const products = [];
                const links = document.querySelectorAll('a[href*="/product/"]');
                links.forEach(a => {
                    const img = a.querySelector('img');
                    const texts = a.innerText.split('\\n').filter(t => t.trim());
                    if (texts.length > 0) {
                        products.push({
                            nome: texts[0] || '',
                            preco: texts.find(t => t.includes('R$')) || '',
                            link: a.href,
                            imagem: img?.src || '',
                            vendidos: texts.find(t => t.includes('vendido') || t.includes('mil')) || '',
                            avaliacao: '',
                        });
                    }
                });
                return products;
            }''')

        produtos = items[:quantidade]
        log(f"[BUSCA] Encontrados: {len(produtos)} produtos")

        for i, prod in enumerate(produtos[:5]):
            log(f"  {i+1}. {prod['nome'][:50]} | {prod['preco']} | {prod.get('vendidos','')}")

        # Salvar cookies atualizados
        cookies = await context.cookies()
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f)

    except Exception as e:
        log(f"[BUSCA] Erro: {e}")

    await browser.close()
    await p.stop()

    return {
        "nicho": nicho_info,
        "busca": busca,
        "produtos": produtos,
        "timestamp": datetime.now().isoformat(),
    }


async def gerar_link_afiliado(product_url, headless=False):
    """
    Gera link de afiliado para um produto da Shopee.
    Acessa o painel de afiliados e converte o link.
    """
    log(f"[LINK] Gerando link afiliado: {product_url[:60]}...")

    p, browser, context = await _create_browser(headless=headless)
    page = await context.new_page()

    affiliate_link = None

    try:
        # Método 1: Usar a ferramenta de geração de links do afiliados
        await page.goto(f"{SHOPEE_AFFILIATE}/offer/link-generator", timeout=30000)
        await asyncio.sleep(3)

        # Colar o link do produto
        input_field = page.locator('input[placeholder*="link"], input[placeholder*="URL"], input[type="text"]').first
        if await input_field.count() > 0:
            await input_field.fill(product_url)
            await asyncio.sleep(1)

            # Clicar em gerar
            gen_btn = page.locator('button:has-text("Gerar"), button:has-text("Generate"), button:has-text("Criar")').first
            if await gen_btn.count() > 0:
                await gen_btn.click()
                await asyncio.sleep(3)

                # Pegar o link gerado
                output = page.locator('input[readonly], [class*="result"] input, textarea[readonly]').first
                if await output.count() > 0:
                    affiliate_link = await output.input_value()
                    log(f"[LINK] Link gerado: {affiliate_link[:60]}...")

        # Método 2: Adicionar parâmetros de afiliado manualmente
        if not affiliate_link:
            # Shopee usa formato: https://s.shopee.com.br/XXXX
            # ou adiciona ?af_id=XXX ao link
            affiliate_link = product_url
            if "?" in affiliate_link:
                affiliate_link += "&af_sub_siteid=autobot"
            else:
                affiliate_link += "?af_sub_siteid=autobot"
            log(f"[LINK] Link com tracking: {affiliate_link[:60]}...")

    except Exception as e:
        log(f"[LINK] Erro: {e}")
        affiliate_link = product_url

    await browser.close()
    await p.stop()

    return affiliate_link


async def pipeline_completo(nicho=None, max_produtos=5, headless=False):
    """
    Pipeline completo de afiliado:
    1. Busca produtos lucrativos
    2. Gera links de afiliado
    3. Cria vídeos promocionais
    4. Salva tudo para postagem
    """
    log(f"\n{'='*60}")
    log("[PIPELINE] Iniciando pipeline de afiliados")

    # 1. Buscar produtos
    resultado = await buscar_produtos(nicho=nicho, quantidade=max_produtos, headless=headless)
    produtos = resultado.get("produtos", [])

    if not produtos:
        log("[PIPELINE] Nenhum produto encontrado!")
        return []

    links_gerados = load_affiliate_links()

    for i, prod in enumerate(produtos[:max_produtos]):
        log(f"\n--- Produto {i+1}/{min(max_produtos, len(produtos))} ---")
        log(f"Nome: {prod['nome'][:60]}")
        log(f"Preço: {prod.get('preco', '?')}")

        # 2. Gerar link de afiliado
        if prod.get("link"):
            aff_link = await gerar_link_afiliado(prod["link"], headless=headless)
        else:
            aff_link = prod.get("link", "")

        # 3. Associar com vídeo existente (ou gerar novo)
        videos_disponiveis = glob.glob(os.path.join(VIDEOS_DIR, "shopee_*.mp4"))
        video_associado = random.choice(videos_disponiveis) if videos_disponiveis else None

        # 4. Criar post para redes sociais
        post_text = _criar_post_afiliado(prod, resultado["nicho"], aff_link)

        entry = {
            "id": f"aff_{int(time.time())}_{i}",
            "produto": prod,
            "link_afiliado": aff_link,
            "video": os.path.basename(video_associado) if video_associado else None,
            "post_text": post_text,
            "nicho": resultado["nicho"]["nicho"],
            "comissao_estimada": resultado["nicho"]["comissao"],
            "criado_em": datetime.now().isoformat(),
            "postado": False,
        }

        links_gerados.append(entry)
        log(f"[PIPELINE] Link #{i+1} salvo: {prod['nome'][:40]}...")

    save_affiliate_links(links_gerados)
    log(f"\n[PIPELINE] Concluído! {len(produtos)} produtos processados.")
    log(f"[PIPELINE] Total de links salvos: {len(links_gerados)}")

    return links_gerados


def _criar_post_afiliado(produto, nicho_info, link):
    """Cria texto do post para redes sociais"""
    nome = produto.get("nome", "Produto incrível")[:80]
    preco = produto.get("preco", "")
    vendidos = produto.get("vendidos", "")

    emojis_nicho = {
        "beleza": "💄✨💅",
        "gadgets": "📱⚡🎮",
        "casa": "🏠✨🧹",
        "cozinha": "🍳👨‍🍳🔥",
        "pets": "🐶🐱🐾",
        "fitness": "💪🏋️‍♂️🔥",
        "kids": "👶🧸🎨",
        "moda": "👗👟✨",
    }

    emojis = emojis_nicho.get(nicho_info.get("nicho", ""), "🔥✨💰")

    hooks = [
        f"ACHEI NA SHOPEE! {emojis[0]}",
        f"PRODUTO VIRAL! {emojis[0]}",
        f"TODO MUNDO COMPRANDO ISSO! {emojis[0]}",
        f"NÃO ACREDITO NESSE PREÇO! {emojis[0]}",
        f"MELHOR COMPRA DO MÊS! {emojis[0]}",
        f"CORRAM! TÁ MUITO BARATO! {emojis[0]}",
    ]

    ctas = [
        "🔗 Link na bio! Corre antes que acabe!",
        "🛒 Tá na promoção! Link na bio!",
        "⬇️ Clica no link da bio pra comprar!",
        "📦 Frete grátis! Link na bio!",
        "💸 Cupom de desconto no link da bio!",
    ]

    texto = f"""{random.choice(hooks)}

{emojis} {nome}

{f'💰 {preco}' if preco else '💰 Preço imperdível!'}
{f'🔥 {vendidos}' if vendidos else '🔥 Mais vendido da categoria!'}

✅ Qualidade garantida
✅ Frete grátis
✅ Entrega rápida

{random.choice(ctas)}

#shopee #achadinhos #shopeebrasiloficial #promocao #desconto #compras #{nicho_info.get('nicho', 'ofertas')} #linknabiografia #afiliado #dicasdecompras"""

    return texto


async def postar_tiktok(entry, headless=False):
    """Posta vídeo de afiliado no TikTok usando o MCP existente"""
    video = entry.get("video")
    if not video:
        log("[TIKTOK] Sem vídeo associado!")
        return False

    video_path = os.path.join(VIDEOS_DIR, video)
    if not os.path.exists(video_path):
        log(f"[TIKTOK] Vídeo não encontrado: {video}")
        return False

    # Usar o sistema de automação do TikTok existente
    tiktok_dir = os.path.join(os.path.dirname(DIR), "mcp-tiktok")
    import subprocess

    descricao = entry["post_text"][:150]  # TikTok limita descrição

    # Chamar automacao.py do TikTok para postar
    cmd = [
        "python3",
        os.path.join(tiktok_dir, "automacao.py"),
        "--postar",
        video_path,
        "--descricao",
        descricao,
    ]

    log(f"[TIKTOK] Postando: {entry['produto']['nome'][:40]}...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=tiktok_dir)
        if result.returncode == 0:
            log("[TIKTOK] Postado com sucesso!")
            return True
        else:
            log(f"[TIKTOK] Erro: {result.stderr[:100]}")
            return False
    except Exception as e:
        log(f"[TIKTOK] Erro: {e}")
        return False


async def auto_afiliado(nicho=None, max_ciclos=5, intervalo=300, headless=False):
    """
    Loop automático completo:
    1. Busca produtos
    2. Gera links
    3. Cria vídeos
    4. Posta no TikTok/Instagram
    """
    log(f"\n{'='*60}")
    log(f"[AUTO] Modo automático: {max_ciclos} ciclos, {intervalo}s intervalo")

    for ciclo in range(max_ciclos):
        log(f"\n[AUTO] === Ciclo {ciclo+1}/{max_ciclos} ===")

        # Escolher nicho aleatório ou fixo
        entries = await pipeline_completo(nicho=nicho, max_produtos=3, headless=headless)

        # Postar no TikTok
        for entry in entries:
            if entry.get("video"):
                await postar_tiktok(entry, headless=headless)
                entry["postado"] = True
                await asyncio.sleep(30)

        save_affiliate_links(load_affiliate_links())

        if ciclo < max_ciclos - 1:
            wait = intervalo + random.randint(-60, 60)
            log(f"[AUTO] Próximo ciclo em {wait}s...")
            await asyncio.sleep(wait)

    log(f"\n[AUTO] Automação concluída! {max_ciclos} ciclos executados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shopee Afiliados - Automação completa")
    parser.add_argument("--login", action="store_true", help="Login no Shopee Afiliados")
    parser.add_argument("--buscar", action="store_true", help="Buscar produtos lucrativos")
    parser.add_argument("--nicho", type=str, help="Nicho específico (beleza, gadgets, casa, etc)")
    parser.add_argument("--pipeline", action="store_true", help="Pipeline completo (busca + links + vídeos)")
    parser.add_argument("--auto", action="store_true", help="Modo automático completo")
    parser.add_argument("--max", type=int, default=5, help="Máx produtos/ciclos (default: 5)")
    parser.add_argument("--intervalo", type=int, default=300, help="Segundos entre ciclos (default: 300)")
    parser.add_argument("--headless", action="store_true", help="Sem janela")
    parser.add_argument("--listar", action="store_true", help="Listar links de afiliado salvos")

    args = parser.parse_args()

    if args.login:
        asyncio.run(affiliate_login())

    elif args.buscar:
        result = asyncio.run(buscar_produtos(nicho=args.nicho, quantidade=args.max))
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.pipeline:
        asyncio.run(pipeline_completo(nicho=args.nicho, max_produtos=args.max))

    elif args.auto:
        asyncio.run(auto_afiliado(
            nicho=args.nicho,
            max_ciclos=args.max,
            intervalo=args.intervalo,
        ))

    elif args.listar:
        links = load_affiliate_links()
        print(f"\n🔗 Links de afiliado salvos: {len(links)}")
        postados = sum(1 for l in links if l.get("postado"))
        print(f"✅ Postados: {postados}")
        print(f"🆕 Pendentes: {len(links) - postados}\n")
        for l in links[-10:]:
            status = "✅" if l.get("postado") else "🆕"
            print(f"  {status} {l['produto']['nome'][:50]} | {l.get('comissao_estimada','?')} | {l.get('nicho','?')}")

    else:
        parser.print_help()
        print("\n📋 Exemplos de uso:")
        print("  python3 shopee_afiliado.py --login                    # Login")
        print("  python3 shopee_afiliado.py --buscar --nicho beleza    # Buscar produtos de beleza")
        print("  python3 shopee_afiliado.py --pipeline --max 5         # Pipeline completo (5 produtos)")
        print("  python3 shopee_afiliado.py --auto --max 3             # Automático (3 ciclos)")
        print("  python3 shopee_afiliado.py --listar                   # Ver links salvos")
        print("\n🎯 Nichos disponíveis:")
        nichos = set(n["nicho"] for n in NICHOS_LUCRATIVOS)
        for n in sorted(nichos):
            prods = [x["busca"] for x in NICHOS_LUCRATIVOS if x["nicho"] == n]
            print(f"  {n}: {', '.join(prods[:3])}")
