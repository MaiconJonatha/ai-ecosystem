#!/usr/bin/env python3
"""
Sistema de Agentes e Subagentes para Shopee Affiliate + Vídeos
- Agente Principal: Coordenador do pipeline
- Subagente 1: Buscador de Produtos
- Subagente 2: Gerador de Links de Afiliado
- Subagente 3: Uploader de Vídeos
- Subagente 4: Gerador de Conteúdo (texto/descrição)
"""
import asyncio, json, os, sys, subprocess, time, random, hashlib, glob, re
from datetime import datetime
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1)
DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

# === CONFIG ===
AFFILIATE_FILE = "affiliate_links.json"
POSTS_LOG = "affiliate_posts_log.json"
AGENT_LOG = "agent_activity.json"

CATEGORIAS = {
    "Mobile & Gadgets": ["fone bluetooth", "carregador turbo", "capinha celular", "power bank", "smartwatch"],
    "Beauty": ["perfume importado", "kit maquiagem", "hidratante facial", "protetor solar", "serum vitamina c"],
    "Home Appliances": ["airfryer", "aspirador robo", "cafeteira", "ventilador torre", "panela eletrica"],
    "Gaming & Consoles": ["mouse gamer", "teclado mecanico", "headset gamer", "controle ps5", "mousepad gamer"],
    "Audio": ["fone gamer", "caixa som bluetooth", "microfone condensador", "soundbar", "earbuds"],
    "Fashion Accessories": ["relogio smartwatch", "oculos sol", "cinto couro", "pulseira smart"],
    "Women Clothes": ["vestido", "blusa feminina", "calca legging", "conjunto fitness"],
    "Men Clothes": ["camiseta masculina", "jaqueta", "bermuda", "polo masculina"],
    "Pets": ["racao premium", "brinquedo pet", "cama cachorro", "coleira led"],
    "Health": ["whey protein", "creatina", "vitamina c", "colageno", "termogenico"],
}

# === UTILITIES ===
def log(agent_name, msg):
    print(f"[{agent_name}] {msg}")

def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default if default is not None else []

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def run_js(js, timeout=20):
    """Executa JS no Chrome via AppleScript"""
    escaped = js.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    script = f'tell application "Google Chrome"\n  tell active tab of front window\n    execute javascript "{escaped}"\n  end tell\nend tell'
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else None
    except:
        return None

def nav(url):
    script = f'tell application "Google Chrome"\n  tell active tab of front window\n    set URL to "{url}"\n  end tell\nend tell'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=15)
    except:
        pass

def get_chrome_url():
    try:
        r = subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to get URL of active tab of front window'],
                          capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except:
        return ""

def get_videos():
    videos = []
    for pattern in ["static/videos/*.mp4", "videos/*.mp4"]:
        videos.extend(glob.glob(pattern))
    return sorted(videos, key=os.path.getmtime, reverse=True)


# ============================================
# SUBAGENTE 1: BUSCADOR DE PRODUTOS
# ============================================
class AgenteBuscador:
    """Busca produtos no Shopee por categoria/termo"""
    
    def __init__(self):
        self.name = "🔍 BUSCADOR"
    
    def buscar(self, termo, limit=5):
        log(self.name, f"Buscando: '{termo}'...")
        nav(f"https://shopee.com.br/search?keyword={quote(termo)}&sortBy=sales")
        time.sleep(8)
        
        result = run_js("""
            var links = [];
            document.querySelectorAll('a').forEach(function(a) {
                var href = a.href || '';
                if (href.indexOf('-i.') >= 0 && href.indexOf('shopee.com.br') >= 0) {
                    var match = href.match(/(https:\\/\\/shopee\\.com\\.br\\/[^?]+)/);
                    if (match) links.push(match[1]);
                }
            });
            JSON.stringify([...new Set(links)].slice(0, """ + str(limit) + """));
        """)
        
        if result:
            try:
                urls = json.loads(result)
                prods = []
                for u in urls:
                    name = u.split("/")[-1].split("-i.")[0].replace("-", " ")
                    prods.append({"titulo": name[:60], "url": u, "termo": termo})
                log(self.name, f"Encontrados: {len(prods)} produtos")
                return prods
            except:
                pass
        
        log(self.name, f"Nenhum produto encontrado para '{termo}'")
        return []
    
    def buscar_multi(self, categorias=None, limit_per_cat=5):
        """Busca em múltiplas categorias"""
        if not categorias:
            categorias = random.sample(list(CATEGORIAS.keys()), min(3, len(CATEGORIAS)))
        
        todos_produtos = []
        for cat in categorias:
            termos = CATEGORIAS.get(cat, ["produto"])
            termo = random.choice(termos)
            prods = self.buscar(termo, limit=limit_per_cat)
            for p in prods:
                p["categoria"] = cat
            todos_produtos.extend(prods)
            time.sleep(2)
        
        return todos_produtos


# ============================================
# SUBAGENTE 2: GERADOR DE LINKS DE AFILIADO
# ============================================
class AgenteAfiliado:
    """Gera links de afiliado via Shopee Affiliate Dashboard"""
    
    def __init__(self):
        self.name = "🔗 AFILIADO"
    
    def gerar_links(self, urls):
        """Gera links de afiliado para até 5 URLs"""
        if not urls:
            return []
        
        log(self.name, f"Gerando links para {len(urls)} produtos...")
        nav("https://affiliate.shopee.com.br/offer/custom_link")
        time.sleep(6)
        
        # Verificar se textarea existe
        has_ta = run_js("document.querySelector('textarea.ant-input') ? 'YES' : 'NO'")
        if has_ta != "YES":
            time.sleep(5)
            has_ta = run_js("document.querySelector('textarea.ant-input') ? 'YES' : 'NO'")
            if has_ta != "YES":
                log(self.name, "Textarea não encontrada - sessão pode ter expirado")
                return []
        
        urls_str = "\\n".join(urls[:5])
        run_js(f"""
            var ta = document.querySelector('textarea.ant-input');
            if (ta) {{
                ta.focus();
                var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                setter.call(ta, '{urls_str}');
                ta.dispatchEvent(new Event('input', {{bubbles: true}}));
                ta.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
            'ok';
        """)
        time.sleep(1)
        
        # Clicar Obter link
        run_js("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if ((btns[i].textContent || '').indexOf('Obter link') >= 0) {
                    btns[i].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                    break;
                }
            }
            'ok';
        """)
        time.sleep(5)
        
        # Extrair links do modal
        result = run_js("""
            var modal = document.querySelector('.ant-modal');
            if (modal) {
                var inputs = modal.querySelectorAll('input, textarea');
                var links = [];
                inputs.forEach(function(el) {
                    var val = (el.value || '').trim();
                    if (val.indexOf('s.shopee') >= 0 || val.indexOf('shp.ee') >= 0) {
                        links.push(val);
                    }
                });
                JSON.stringify(links);
            } else { '[]'; }
        """)
        
        links = []
        if result:
            try:
                links = json.loads(result)
            except:
                pass
        
        # Fechar modal
        run_js("var c = document.querySelector('.ant-modal-close'); if(c) c.click(); 'ok';")
        time.sleep(1)
        
        log(self.name, f"Links gerados: {len(links)}")
        return links


# ============================================
# SUBAGENTE 3: UPLOADER DE VÍDEOS NO SHOPEE
# ============================================
class AgenteUploader:
    """Upload de vídeos no Shopee Creator Center"""
    
    def __init__(self):
        self.name = "📤 UPLOADER"
    
    def abrir_creator_center(self):
        log(self.name, "Abrindo Creator Center > Vídeo...")
        nav("https://seller.shopee.com.br/creator-center/insight/video")
        time.sleep(15)
        
        url = get_chrome_url()
        if "login" in url.lower():
            log(self.name, "⚠️ Sessão expirada! Recarregando seller center...")
            nav("https://seller.shopee.com.br/")
            time.sleep(10)
            nav("https://seller.shopee.com.br/creator-center/insight/video")
            time.sleep(15)
        
        return get_chrome_url()
    
    def encontrar_upload(self):
        """Procura o botão/link de Enviar Vídeo"""
        # Esperar conteúdo carregar
        for i in range(5):
            html_len = run_js("document.body.innerHTML.length")
            enviar_idx = run_js("document.body.innerHTML.indexOf('Enviar V')")
            log(self.name, f"HTML: {html_len} bytes, Enviar idx: {enviar_idx}")
            if enviar_idx and int(enviar_idx) > 0:
                break
            time.sleep(5)
        
        # Clicar em Enviar Vídeo
        clicked = run_js("""
            var els = document.querySelectorAll('a, button, div, span');
            for (var i = 0; i < els.length; i++) {
                var t = (els[i].textContent || '').trim();
                if (t === 'Enviar Vídeo' || t === 'Upload Video') {
                    els[i].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                    break;
                }
            }
            'done';
        """)
        time.sleep(5)
        
        url = get_chrome_url()
        log(self.name, f"URL após click: {url}")
        return url
    
    def upload_video(self, video_path, titulo="", descricao="", produto_url=""):
        """Faz upload de um vídeo e preenche os dados"""
        log(self.name, f"Upload: {os.path.basename(video_path)}")
        
        # Verificar file inputs
        file_count = run_js("document.querySelectorAll('input[type=file]').length")
        log(self.name, f"File inputs: {file_count}")
        
        if file_count and int(file_count) > 0:
            # Não podemos usar set_input_files via AppleScript
            # Usar drag & drop ou outra técnica
            log(self.name, "⚠️ Upload via AppleScript limitado - use Playwright")
        
        return False


# ============================================
# SUBAGENTE 4: GERADOR DE CONTEÚDO
# ============================================
class AgenteConteudo:
    """Gera textos, descrições e hashtags para posts"""
    
    def __init__(self):
        self.name = "✍️ CONTEÚDO"
    
    def gerar_post(self, produto, link_afiliado, plataforma="shopee"):
        """Gera texto de post para o produto"""
        titulo = produto.get("titulo", "Produto Incrível")
        categoria = produto.get("categoria", "")
        url = link_afiliado or produto.get("url", "")
        
        emojis_cat = {
            "Mobile & Gadgets": "📱⚡", "Beauty": "✨💄", "Gaming & Consoles": "🎮🕹️",
            "Audio": "🎧🔊", "Health": "💪🏋️", "Pets": "🐶🐱", "Home Appliances": "🏠✨",
            "Fashion Accessories": "💎👗", "Women Clothes": "👠👗", "Men Clothes": "👔🧥",
        }
        emoji = emojis_cat.get(categoria, "🔥🛒")
        
        templates = [
            f"{emoji} ACHADO INCRÍVEL!\n\n{titulo}\n\n🔥 Melhor preço da Shopee!\n✅ Frete Grátis\n🛡️ Garantia Shopee\n\n👉 Link na bio\n{url}\n\n#shopee #oferta #desconto #achadinhos #compras",
            f"⚡ CORRE ANTES QUE ACABE! {emoji}\n\n{titulo}\n\n💰 Preço mais baixo!\n📦 Entrega rápida\n⭐ Avaliação TOP\n\n{url}\n\n#promocao #shopee #achados #barato",
            f"PARE TUDO! {emoji}\n\n{titulo}\n\nOferta IMPERDÍVEL! 🤯\n\nCompre agora:\n{url}\n\n#shopee #achei #melhoresprecos #comprasinteligentes",
        ]
        
        return random.choice(templates)
    
    def gerar_descricao_video(self, produto, link_afiliado):
        """Gera descrição para vídeo no Shopee"""
        titulo = produto.get("titulo", "")
        url = link_afiliado or ""
        
        return f"""🔥 {titulo}

✅ Melhor preço da Shopee!
✅ Frete Grátis
✅ Garantia Shopee

🛒 Compre agora pelo link!

#shopee #oferta #achadinhos"""


# ============================================
# AGENTE PRINCIPAL: COORDENADOR
# ============================================
class AgenteCoordenador:
    """Coordena todos os subagentes para executar a pipeline"""
    
    def __init__(self):
        self.name = "🤖 COORDENADOR"
        self.buscador = AgenteBuscador()
        self.afiliado = AgenteAfiliado()
        self.uploader = AgenteUploader()
        self.conteudo = AgenteConteudo()
    
    def status(self):
        """Mostra status do sistema"""
        links = load_json(AFFILIATE_FILE, [])
        posts = load_json(POSTS_LOG, [])
        videos = get_videos()
        
        com_link = sum(1 for l in links if l.get("url_afiliado"))
        postados = sum(1 for l in links if l.get("postado"))
        
        print(f"""
╔════════════════════════════════════════════╗
║     SHOPEE AFFILIATE AGENT SYSTEM          ║
╠════════════════════════════════════════════╣
║ 🔗 Links de afiliado:  {com_link:>4} / {len(links):<4}       ║
║ 📤 Já postados:        {postados:>4}               ║
║ 📝 Posts gerados:      {len(posts):>4}               ║
║ 🎬 Vídeos disponíveis: {len(videos):>4}               ║
║ 📂 Categorias:         {len(CATEGORIAS):>4}               ║
╠════════════════════════════════════════════╣
║ Agentes: Buscador | Afiliado | Uploader   ║
║          Conteúdo | Coordenador           ║
╚════════════════════════════════════════════╝
        """)
    
    def pipeline_buscar_e_gerar(self, categorias=None, max_produtos=10):
        """Pipeline: buscar produtos + gerar links de afiliado"""
        log(self.name, "Iniciando pipeline BUSCAR + GERAR LINKS")
        
        # 1. Buscar produtos
        produtos = self.buscador.buscar_multi(categorias=categorias, limit_per_cat=5)
        if not produtos:
            log(self.name, "Nenhum produto encontrado!")
            return 0
        
        # 2. Filtrar duplicados
        existing = load_json(AFFILIATE_FILE, [])
        existing_urls = {l.get("url_original", "") for l in existing}
        novos = [p for p in produtos if p["url"] not in existing_urls]
        
        if not novos:
            log(self.name, "Todos os produtos já cadastrados!")
            return 0
        
        log(self.name, f"{len(novos)} novos produtos para processar")
        
        # 3. Gerar links de afiliado (em lotes de 5)
        total_novos = 0
        for i in range(0, len(novos), 5):
            lote = novos[i:i+5]
            urls = [p["url"] for p in lote]
            
            aff_links = self.afiliado.gerar_links(urls)
            
            for j, prod in enumerate(lote):
                aff = aff_links[j] if j < len(aff_links) else None
                entry = {
                    "id": hashlib.md5(prod["url"].encode()).hexdigest()[:8],
                    "categoria": prod.get("categoria", prod.get("termo", "")),
                    "titulo": prod["titulo"],
                    "url_original": prod["url"],
                    "url_afiliado": aff,
                    "data": datetime.now().isoformat(),
                    "postado": False,
                }
                existing.append(entry)
                total_novos += 1
                status = "✅" if aff else "❌"
                log(self.name, f"  {status} {prod['titulo'][:40]}")
            
            save_json(AFFILIATE_FILE, existing)
            
            if total_novos >= max_produtos:
                break
            time.sleep(2)
        
        log(self.name, f"Pipeline concluída! {total_novos} novos produtos. Total: {len(existing)}")
        return total_novos
    
    def pipeline_gerar_posts(self, limit=10):
        """Gera posts para links não postados"""
        log(self.name, "Gerando posts para links pendentes...")
        
        links = load_json(AFFILIATE_FILE, [])
        posts = load_json(POSTS_LOG, [])
        
        pendentes = [l for l in links if not l.get("postado") and l.get("url_afiliado")]
        
        if not pendentes:
            log(self.name, "Nenhum link pendente!")
            return 0
        
        gerados = 0
        for link in pendentes[:limit]:
            texto = self.conteudo.gerar_post(link, link.get("url_afiliado"))
            
            posts.append({
                "link_id": link["id"],
                "texto": texto,
                "data": datetime.now().isoformat(),
                "plataforma": "shopee_video",
                "video": None,
            })
            
            # Associar vídeo
            videos = get_videos()
            if videos:
                video = random.choice(videos[:20])  # Pegar dos 20 mais recentes
                posts[-1]["video"] = video
            
            link["postado"] = True
            gerados += 1
            
            print(f"\n{'─'*40}")
            print(f"📝 Post #{gerados}:")
            print(texto)
            if posts[-1].get("video"):
                print(f"🎬 Vídeo: {os.path.basename(posts[-1]['video'])}")
            print(f"{'─'*40}")
        
        save_json(AFFILIATE_FILE, links)
        save_json(POSTS_LOG, posts)
        
        log(self.name, f"{gerados} posts gerados!")
        return gerados
    
    def pipeline_completa(self, categorias=None, max_produtos=10):
        """Pipeline completa: buscar + gerar links + gerar posts"""
        log(self.name, "═══ PIPELINE COMPLETA ═══")
        
        novos = self.pipeline_buscar_e_gerar(categorias=categorias, max_produtos=max_produtos)
        
        if novos > 0:
            self.pipeline_gerar_posts(limit=novos)
        
        self.status()
    
    def auto(self, intervalo=1800, max_ciclos=10):
        """Modo automático contínuo"""
        log(self.name, f"🚀 MODO AUTOMÁTICO | Intervalo: {intervalo}s | Ciclos: {max_ciclos}")
        
        for ciclo in range(max_ciclos):
            print(f"\n{'═'*60}")
            log(self.name, f"Ciclo {ciclo+1}/{max_ciclos} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'═'*60}")
            
            cats = random.sample(list(CATEGORIAS.keys()), min(2, len(CATEGORIAS)))
            self.pipeline_completa(categorias=cats, max_produtos=5)
            
            if ciclo < max_ciclos - 1:
                log(self.name, f"Próximo ciclo em {intervalo}s...")
                time.sleep(intervalo)
        
        log(self.name, "Pipeline automática finalizada!")
    
    def listar_links(self):
        """Lista todos os links de afiliado"""
        links = load_json(AFFILIATE_FILE, [])
        print(f"\n📊 Total: {len(links)} links")
        for l in links:
            s = "✅" if l.get("url_afiliado") else "❌"
            p = "📤" if l.get("postado") else "⏳"
            url = l.get("url_afiliado", "sem link")
            print(f"  {s}{p} [{l.get('categoria','')}] {l.get('titulo','')[:35]} | {url}")


# === CLI ===
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Shopee Affiliate Agent System")
    parser.add_argument("--status", action="store_true", help="Status do sistema")
    parser.add_argument("--buscar", type=str, help="Buscar produtos (categoria ou termo)")
    parser.add_argument("--pipeline", action="store_true", help="Pipeline completa")
    parser.add_argument("--posts", action="store_true", help="Gerar posts pendentes")
    parser.add_argument("--auto", action="store_true", help="Modo automático")
    parser.add_argument("--listar", action="store_true", help="Listar links")
    parser.add_argument("--categorias", type=str, help="Categorias (comma separated)")
    parser.add_argument("--intervalo", type=int, default=1800, help="Intervalo auto (seg)")
    parser.add_argument("--max", type=int, default=10, help="Max produtos/ciclos")
    args = parser.parse_args()
    
    coord = AgenteCoordenador()
    
    cats = args.categorias.split(",") if args.categorias else None
    
    if args.status:
        coord.status()
    elif args.listar:
        coord.listar_links()
    elif args.buscar:
        if args.buscar in CATEGORIAS:
            prods = coord.buscador.buscar_multi(categorias=[args.buscar])
        else:
            prods = coord.buscador.buscar(args.buscar, limit=args.max)
        for p in prods:
            print(f"  🛒 {p['titulo'][:45]} | {p['url'][:60]}")
    elif args.posts:
        coord.pipeline_gerar_posts(limit=args.max)
    elif args.pipeline:
        coord.pipeline_completa(categorias=cats, max_produtos=args.max)
    elif args.auto:
        coord.auto(intervalo=args.intervalo, max_ciclos=args.max)
    else:
        coord.status()
        print("\nComandos: --status | --buscar TERMO | --pipeline | --posts | --auto | --listar")
