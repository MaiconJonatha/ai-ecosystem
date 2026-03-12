#!/usr/bin/env python3
"""
Enriquece vídeos pendentes com nomes reais dos produtos.
Usa Chrome para acessar cada link e extrair nome/preço do produto.
"""
import json, os, sys, time, subprocess, re
import httpx

try:
    sys.stdout.reconfigure(line_buffering=True)
except:
    pass

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

PENDING_FILE = os.path.join(DIR, "telegram_pending.json")


def run_js(js):
    escaped = js.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    script = f'tell application "Google Chrome"\n  tell active tab of front window\n    execute javascript "{escaped}"\n  end tell\nend tell'
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else None
    except:
        return None


def nav(url):
    script = f'tell application "Google Chrome"\n  tell active tab of front window\n    set URL to "{url}"\n  end tell\nend tell'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=15)
        return True
    except:
        return False


def chrome_available():
    try:
        r = subprocess.run(["osascript", "-e", 'tell application "System Events" to (name of processes) contains "Google Chrome"'],
                          capture_output=True, text=True, timeout=5)
        return "true" in r.stdout.lower()
    except:
        return False


def extract_product_from_url(url):
    """Extrai nome do produto da URL (para links -i.)"""
    if not url:
        return None
    for part in url.split("/"):
        if "-i." in part:
            name = part.split("-i.")[0].replace("-", " ")
            # Decodificar URL encoding
            from urllib.parse import unquote
            name = unquote(name)
            return name[:80] if len(name) > 3 else None
    return None


def resolve_link(short_url):
    """Resolve link curto -> URL real"""
    if not short_url:
        return None
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            resp = client.head(short_url)
            return str(resp.url).split("?")[0]
    except:
        return None


def get_product_name_chrome(url):
    """Acessa pagina no Chrome e extrai nome do produto"""
    if not nav(url):
        return None
    time.sleep(5)
    
    # Tentar varias estrategias para pegar o nome
    result = run_js("""
        // Estrategia 1: titulo da pagina
        let name = document.title || '';
        name = name.replace(/\\s*[-|]\\s*Shopee.*$/i, '').trim();
        
        // Estrategia 2: meta og:title
        if (!name || name.length < 5) {
            const og = document.querySelector('meta[property="og:title"]');
            if (og) name = og.content || '';
        }
        
        // Estrategia 3: h1 ou elemento de nome do produto
        if (!name || name.length < 5) {
            const h1 = document.querySelector('h1, [data-testid="product-name"], .product-name, ._2rQP1z');
            if (h1) name = h1.textContent || '';
        }
        
        // Estrategia 4: primeiro texto grande na pagina
        if (!name || name.length < 5) {
            const els = document.querySelectorAll('span, div, p');
            for (const el of els) {
                const t = (el.textContent || '').trim();
                if (t.length > 10 && t.length < 100 && !t.includes('Shopee') && !t.includes('carrinho')) {
                    name = t;
                    break;
                }
            }
        }
        
        // Pegar preco tambem
        let price = '';
        const priceEl = document.querySelector('[class*="price"], [class*="Price"]');
        if (priceEl) {
            const pt = priceEl.textContent || '';
            const m = pt.match(/R\\$\\s*[\\d.,]+/);
            if (m) price = m[0];
        }
        
        JSON.stringify({name: name.trim().substring(0, 80), price: price});
    """)
    
    if result:
        try:
            data = json.loads(result)
            name = data.get("name", "")
            price = data.get("price", "")
            if name and len(name) > 3:
                return {"name": name, "price": price}
        except:
            pass
    return None


def enrich_all():
    """Enriquece todos os videos pendentes com nomes de produtos"""
    pending = json.load(open(PENDING_FILE))
    
    # Filtrar: sem nome de produto adequado
    need_enrichment = []
    for e in pending:
        link = e.get("shopee_link", "")
        has_product_name = e.get("product_name", "")
        if link and not has_product_name:
            need_enrichment.append(e)
    
    if not need_enrichment:
        print("Todos os videos ja tem nome de produto!")
        return 0
    
    print(f"Videos sem nome de produto: {len(need_enrichment)}\n")
    
    # Cache de URLs ja resolvidas
    url_cache = {}
    name_cache = {}
    enriched = 0
    
    use_chrome = chrome_available()
    print(f"Chrome disponivel: {use_chrome}\n")
    
    for i, entry in enumerate(need_enrichment):
        link = entry.get("shopee_link", "")
        
        # Resolver link
        if link in url_cache:
            real_url = url_cache[link]
        else:
            real_url = resolve_link(link)
            url_cache[link] = real_url
        
        if not real_url:
            continue
        
        # Tentar extrair nome da URL primeiro (rapido)
        name = extract_product_from_url(real_url)
        price = ""
        
        # Se nao tem nome na URL e Chrome disponivel, acessar pagina
        if not name and use_chrome and real_url not in name_cache:
            print(f"  [{i+1}/{len(need_enrichment)}] Chrome: {real_url[:60]}...")
            info = get_product_name_chrome(real_url)
            if info:
                name = info.get("name", "")
                price = info.get("price", "")
                name_cache[real_url] = info
        elif not name and real_url in name_cache:
            info = name_cache[real_url]
            name = info.get("name", "")
            price = info.get("price", "")
        
        if name and len(name) > 3:
            entry["product_name"] = name
            entry["product_price"] = price
            
            # Atualizar descricao
            my_link = entry.get("my_affiliate_link", "") or entry.get("shopee_link", "")
            desc = f"{name}"
            if price:
                desc += f" {price}"
            desc += f"\n#shopee #achadosshopee #shopeefinds #promocao #oferta"
            desc += f"\n{my_link}"
            entry["clean_description"] = desc
            entry["description_updated"] = True
            enriched += 1
            print(f"  [{i+1}] {name[:50]} {price}")
        else:
            # Fallback generico baseado no canal
            channel = entry.get("channel", "")
            text = entry.get("text", "")
            fallback = text.split("https")[0].split("http")[0].strip()
            fallback = re.sub(r'Video \d+:', '', fallback).strip()
            fallback = fallback.split("\n")[0][:60].strip()
            if fallback and len(fallback) > 3:
                entry["product_name"] = fallback
                my_link = entry.get("my_affiliate_link", "") or entry.get("shopee_link", "")
                entry["clean_description"] = f"{fallback}\n#shopee #achadosshopee #shopeefinds #promocao\n{my_link}"
                entry["description_updated"] = True
                enriched += 1
                print(f"  [{i+1}] (fallback) {fallback[:50]}")
    
    # Salvar
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f, indent=2, ensure_ascii=False)
    
    print(f"\nEnriquecidos: {enriched}/{len(need_enrichment)}")
    return enriched


if __name__ == "__main__":
    enrich_all()
