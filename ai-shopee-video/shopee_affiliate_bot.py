#!/usr/bin/env python3
"""
Shopee Affiliate Bot - Automação completa do programa de afiliados
- Busca produtos populares no Shopee
- Gera links de afiliado via Chrome real
- Associa com vídeos existentes
- Posta nas redes sociais (TikTok, Instagram)
"""
import asyncio, json, os, sys, subprocess, time, random, re, glob, hashlib
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)
sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1)

# === CONFIG ===
AFFILIATE_LINKS_FILE = "affiliate_links.json"
POSTS_LOG_FILE = "affiliate_posts_log.json"

# 20 categorias do Shopee Affiliate com termos de busca
CATEGORIAS = {
    "Health": ["suplemento whey", "vitamina c", "colageno", "termogenico", "creatina"],
    "Fashion Accessories": ["relogio smartwatch", "oculos sol", "cinto couro", "pulseira"],
    "Home Appliances": ["airfryer", "aspirador robo", "cafeteira", "ventilador"],
    "Men Clothes": ["camiseta masculina", "jaqueta masculina", "bermuda"],
    "Men Shoes": ["tenis masculino", "sapato social", "chinelo slide"],
    "Mobile & Gadgets": ["carregador turbo", "fone bluetooth", "capinha celular", "power bank"],
    "Travel & Luggage": ["mala viagem", "mochila notebook", "necessaire"],
    "Women Bags": ["bolsa feminina", "mochila feminina", "clutch"],
    "Women Clothes": ["vestido", "blusa feminina", "calca legging"],
    "Food Delivery": ["kit doces", "cesta cafe", "chocolate importado"],
    "Women Shoes": ["tenis feminino", "sandalia", "bota feminina"],
    "Men Bags": ["mochila masculina", "bolsa carteiro", "pochete"],
    "Watches": ["relogio digital", "smartwatch", "relogio esportivo"],
    "Audio": ["fone gamer", "caixa som bluetooth", "microfone condensador"],
    "Food & Beverages": ["cafe especial", "whey protein", "granola"],
    "Beauty": ["perfume importado", "maquiagem kit", "hidratante facial", "protetor solar"],
    "Pets": ["racao premium", "brinquedo pet", "cama cachorro"],
    "Mom & Baby": ["carrinho bebe", "fralda", "mamadeira"],
    "Baby & Kids Fashion": ["roupa infantil", "sapato bebe", "fantasia infantil"],
    "Gaming & Consoles": ["controle ps5", "headset gamer", "teclado mecanico", "mouse gamer"],
}

def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default or []

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def apple_script(js_code):
    """Executa JavaScript no Chrome via AppleScript"""
    escaped = js_code.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    script = f'''
    tell application "Google Chrome"
      tell active tab of front window
        execute javascript "{escaped}"
      end tell
    end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except:
        return None

def navigate(url):
    """Navega o Chrome para uma URL"""
    script = f'''
    tell application "Google Chrome"
      tell active tab of front window
        set URL to "{url}"
      end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)

def get_videos():
    """Lista vídeos disponíveis"""
    videos = []
    for ext in ["*.mp4", "*.webm", "*.mov"]:
        videos.extend(glob.glob(f"static/videos/{ext}"))
        videos.extend(glob.glob(f"videos/{ext}"))
    return sorted(videos, key=os.path.getmtime, reverse=True)

# === CORE FUNCTIONS ===

def buscar_produtos_shopee(categoria=None, termo=None, limit=5):
    """Busca produtos no Shopee via pesquisa"""
    if not termo and categoria:
        termos = CATEGORIAS.get(categoria, ["produto popular"])
        termo = random.choice(termos)
    elif not termo:
        cat = random.choice(list(CATEGORIAS.keys()))
        termos = CATEGORIAS[cat]
        termo = random.choice(termos)
        categoria = cat

    print(f"[BUSCA] Categoria: {categoria} | Termo: {termo}")

    # Navegar para busca no Shopee
    search_url = f"https://shopee.com.br/search?keyword={termo.replace(' ', '+')}"
    navigate(search_url)
    time.sleep(8)

    # Extrair links de produtos
    products = apple_script("""
        const items = document.querySelectorAll('a[data-sqe], a[href*="-i."]');
        const products = [];
        items.forEach(a => {
            const href = a.getAttribute('href') || '';
            const text = (a.innerText || '').trim().substring(0, 100);
            if (href.includes('-i.') && text.length > 5) {
                products.push(JSON.stringify({
                    title: text.split('\\n')[0],
                    url: 'https://shopee.com.br' + href,
                    price: (text.match(/R\\$\\s*[\\d.,]+/) || [''])[0]
                }));
            }
        });
        '[' + products.slice(0, """ + str(limit) + """).join(',') + ']';
    """)

    if products:
        try:
            return json.loads(products)
        except:
            pass

    # Fallback: pegar todos os links de produto
    links = apple_script("""
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.href || '';
            if (href.includes('-i.') && href.includes('shopee.com.br')) {
                links.push(href);
            }
        });
        JSON.stringify([...new Set(links)].slice(0, 10));
    """)
    if links:
        try:
            urls = json.loads(links)
            return [{"title": f"Produto {i+1} - {termo}", "url": u, "price": ""} for i, u in enumerate(urls[:limit])]
        except:
            pass

    print(f"[BUSCA] Nenhum produto encontrado para '{termo}'")
    return []

def gerar_link_afiliado(product_urls):
    """Gera links de afiliado usando a página de Link Personalizado"""
    if not product_urls:
        return []

    print(f"[LINK] Gerando links para {len(product_urls)} produtos...")

    # Navegar para página de link personalizado
    navigate("https://affiliate.shopee.com.br/offer/custom_link")
    time.sleep(5)

    # Preencher os links (até 5 por vez)
    urls_text = "\\n".join(product_urls[:5])
    apple_script(f"""
        const textarea = document.querySelector('textarea');
        if (textarea) {{
            textarea.focus();
            const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            setter.call(textarea, '{urls_text}');
            textarea.dispatchEvent(new Event('input', {{bubbles: true}}));
            textarea.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
        'filled';
    """)
    time.sleep(1)

    # Preencher Sub_ID para tracking
    apple_script("""
        const subId1 = document.getElementById('customLink_sub_id1');
        if (subId1) {
            subId1.focus();
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(subId1, 'AutoBot');
            subId1.dispatchEvent(new Event('input', {bubbles: true}));
        }
        'ok';
    """)
    time.sleep(0.5)

    # Clicar em "Gerar Link" / "Obter link"
    apple_script("""
        const btns = document.querySelectorAll('button');
        for (const btn of btns) {
            const t = (btn.textContent || '').trim();
            if (t.includes('Obter link') || t.includes('Gerar')) {
                btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                break;
            }
        }
        'clicked';
    """)
    time.sleep(5)

    # Extrair links gerados
    result = apple_script("""
        const cells = document.querySelectorAll('td, [class*=link], [class*=result], input[readonly], textarea[readonly]');
        const links = [];
        cells.forEach(el => {
            const val = el.value || el.textContent || '';
            if (val.includes('shp.ee') || val.includes('s.shopee')) {
                links.push(val.trim());
            }
        });
        // Also check for copy buttons or result divs
        document.querySelectorAll('[class*=copy], [class*=result]').forEach(el => {
            const t = (el.textContent || '').trim();
            if (t.includes('shp.ee') || t.includes('s.shopee')) {
                links.push(t);
            }
        });
        JSON.stringify([...new Set(links)]);
    """)

    if result:
        try:
            return json.loads(result)
        except:
            pass

    # Tentar pegar de outra forma
    page_text = apple_script("document.body.innerText.substring(0, 3000)")
    if page_text:
        # Procurar URLs de afiliado no texto
        import re
        affiliate_urls = re.findall(r'https?://(?:shp\.ee|s\.shopee\.com\.br)/\S+', page_text)
        if affiliate_urls:
            return affiliate_urls

    print("[LINK] Não conseguiu extrair links de afiliado")
    return []

def pipeline_completa(categorias=None, max_produtos=10):
    """Pipeline completa: buscar -> gerar links -> salvar"""
    if not categorias:
        categorias = random.sample(list(CATEGORIAS.keys()), min(3, len(CATEGORIAS)))

    all_links = load_json(AFFILIATE_LINKS_FILE, [])
    novos = 0

    for cat in categorias:
        print(f"\n{'='*50}")
        print(f"[PIPELINE] Categoria: {cat}")
        print(f"{'='*50}")

        produtos = buscar_produtos_shopee(categoria=cat, limit=5)
        if not produtos:
            continue

        urls = [p["url"] for p in produtos if p.get("url")]
        if not urls:
            continue

        affiliate_links = gerar_link_afiliado(urls)

        for i, prod in enumerate(produtos):
            link = affiliate_links[i] if i < len(affiliate_links) else None
            entry = {
                "id": hashlib.md5(prod["url"].encode()).hexdigest()[:8],
                "categoria": cat,
                "titulo": prod.get("title", ""),
                "url_original": prod["url"],
                "url_afiliado": link,
                "preco": prod.get("price", ""),
                "data": datetime.now().isoformat(),
                "postado": False,
            }

            # Não duplicar
            if not any(l.get("url_original") == prod["url"] for l in all_links):
                all_links.append(entry)
                novos += 1
                status = "✅ Link de afiliado" if link else "⚠️ Sem link"
                print(f"  {status}: {prod.get('title', '')[:50]}")

        if novos >= max_produtos:
            break

        time.sleep(3)

    save_json(AFFILIATE_LINKS_FILE, all_links)
    print(f"\n[PIPELINE] {novos} novos produtos salvos! Total: {len(all_links)}")
    return novos

def criar_post_social(link_data, video_path=None):
    """Cria texto de post para redes sociais com link de afiliado"""
    titulo = link_data.get("titulo", "Produto Incrível")
    preco = link_data.get("preco", "")
    url = link_data.get("url_afiliado") or link_data.get("url_original", "")
    cat = link_data.get("categoria", "")

    emojis = {
        "Health": "💪🏋️", "Beauty": "✨💄", "Mobile & Gadgets": "📱⚡",
        "Gaming & Consoles": "🎮🕹️", "Audio": "🎧🔊", "Pets": "🐶🐱",
        "Home Appliances": "🏠✨", "Fashion Accessories": "👗💎",
        "Women Clothes": "👠👗", "Men Clothes": "👔🧥",
    }
    emoji = emojis.get(cat, "🔥🛒")

    templates = [
        f"{emoji} {titulo}\n\n💰 {preco}\n🔥 Oferta IMPERDÍVEL na Shopee!\n\n👉 {url}\n\n#shopee #oferta #desconto #achadinhos",
        f"ACHEI O MELHOR PREÇO! {emoji}\n\n{titulo}\n{preco}\n\n✅ Frete Grátis\n✅ Garantia Shopee\n\nLink na bio ou aqui 👇\n{url}\n\n#compras #shopee #barato",
        f"⚡ CORRE QUE ACABA! {emoji}\n\n{titulo} por apenas {preco}!\n\nCompra segura pela Shopee 🛡️\n\n{url}\n\n#promocao #shopee #achados",
    ]

    return random.choice(templates)

def auto_pipeline(intervalo=1800, max_ciclos=10):
    """Loop automático: busca + gera links a cada intervalo"""
    print(f"[AUTO] Iniciando pipeline automática")
    print(f"[AUTO] Intervalo: {intervalo}s | Max ciclos: {max_ciclos}")

    for ciclo in range(max_ciclos):
        print(f"\n{'#'*60}")
        print(f"[AUTO] Ciclo {ciclo+1}/{max_ciclos} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'#'*60}")

        # Selecionar 2-3 categorias aleatórias
        cats = random.sample(list(CATEGORIAS.keys()), min(3, len(CATEGORIAS)))
        novos = pipeline_completa(categorias=cats, max_produtos=5)

        # Gerar posts para links não postados
        all_links = load_json(AFFILIATE_LINKS_FILE, [])
        nao_postados = [l for l in all_links if not l.get("postado") and l.get("url_afiliado")]

        if nao_postados:
            link = nao_postados[0]
            post_text = criar_post_social(link)
            print(f"\n[POST] Texto gerado:")
            print(post_text)

            # Salvar post no log
            posts_log = load_json(POSTS_LOG_FILE, [])
            posts_log.append({
                "link_id": link["id"],
                "texto": post_text,
                "data": datetime.now().isoformat(),
                "plataforma": "pendente",
            })
            save_json(POSTS_LOG_FILE, posts_log)

            # Marcar como postado
            link["postado"] = True
            save_json(AFFILIATE_LINKS_FILE, all_links)

        if ciclo < max_ciclos - 1:
            print(f"\n[AUTO] Próximo ciclo em {intervalo}s...")
            time.sleep(intervalo)

    print(f"\n[AUTO] Pipeline finalizada!")

def listar_links():
    """Lista todos os links de afiliado salvos"""
    links = load_json(AFFILIATE_LINKS_FILE, [])
    print(f"\n📊 Total de links: {len(links)}")
    for l in links:
        status = "✅" if l.get("url_afiliado") else "❌"
        postado = "📤" if l.get("postado") else "⏳"
        print(f"  {status}{postado} [{l.get('categoria', '')}] {l.get('titulo', '')[:40]} {l.get('preco', '')}")
    return links

def status():
    """Mostra status do sistema"""
    links = load_json(AFFILIATE_LINKS_FILE, [])
    posts = load_json(POSTS_LOG_FILE, [])
    videos = get_videos()

    com_link = sum(1 for l in links if l.get("url_afiliado"))
    postados = sum(1 for l in links if l.get("postado"))

    print(f"""
╔══════════════════════════════════════╗
║   SHOPEE AFFILIATE BOT - STATUS     ║
╠══════════════════════════════════════╣
║ Links salvos:     {len(links):>4}              ║
║ Com link afiliado:{com_link:>4}              ║
║ Já postados:      {postados:>4}              ║
║ Posts gerados:    {len(posts):>4}              ║
║ Vídeos disponíveis:{len(videos):>4}             ║
║ Categorias:       {len(CATEGORIAS):>4}              ║
╚══════════════════════════════════════╝
    """)

# === CLI ===
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Shopee Affiliate Bot")
    parser.add_argument("--buscar", type=str, help="Buscar produtos (categoria ou termo)")
    parser.add_argument("--pipeline", action="store_true", help="Executar pipeline completa")
    parser.add_argument("--auto", action="store_true", help="Modo automático contínuo")
    parser.add_argument("--listar", action="store_true", help="Listar links salvos")
    parser.add_argument("--status", action="store_true", help="Mostrar status")
    parser.add_argument("--gerar-link", type=str, help="Gerar link de afiliado para URL")
    parser.add_argument("--post", type=str, help="Gerar post social para link ID")
    parser.add_argument("--intervalo", type=int, default=1800, help="Intervalo entre ciclos (seg)")
    parser.add_argument("--max", type=int, default=10, help="Max ciclos ou produtos")
    args = parser.parse_args()

    if args.status:
        status()
    elif args.listar:
        listar_links()
    elif args.buscar:
        # Verificar se é categoria ou termo livre
        if args.buscar in CATEGORIAS:
            produtos = buscar_produtos_shopee(categoria=args.buscar, limit=args.max)
        else:
            produtos = buscar_produtos_shopee(termo=args.buscar, limit=args.max)
        for p in produtos:
            print(f"  🛒 {p.get('title', '')[:50]} | {p.get('price', '')} | {p.get('url', '')[:60]}")
    elif args.gerar_link:
        links = gerar_link_afiliado([args.gerar_link])
        for l in links:
            print(f"  🔗 {l}")
    elif args.pipeline:
        pipeline_completa(max_produtos=args.max)
    elif args.auto:
        auto_pipeline(intervalo=args.intervalo, max_ciclos=args.max)
    elif args.post:
        all_links = load_json(AFFILIATE_LINKS_FILE, [])
        found = [l for l in all_links if l.get("id") == args.post]
        if found:
            print(criar_post_social(found[0]))
        else:
            print(f"Link ID '{args.post}' não encontrado")
    else:
        status()
        print("Use --help para ver os comandos disponíveis")
