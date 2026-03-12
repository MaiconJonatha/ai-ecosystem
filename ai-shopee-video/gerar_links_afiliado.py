#!/usr/bin/env python3
"""Gera links de afiliado em massa - busca no Shopee + gera via Affiliate Dashboard"""
import subprocess, json, time, os, sys, hashlib, random, re
from datetime import datetime
from urllib.parse import quote

sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1)
DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

TERMOS_LUCRATIVOS = [
    "airfryer", "smartwatch", "fone bluetooth", "perfume importado",
    "maquiagem kit", "tenis nike", "mouse gamer", "teclado mecanico",
    "headset gamer", "power bank", "carregador turbo", "camiseta masculina",
    "vestido feminino", "bolsa feminina", "relogio digital",
    "protetor solar", "hidratante facial", "whey protein",
    "creatina", "aspirador robo"
]

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
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=15)

def buscar_links_produto(termo, limit=5):
    """Busca produtos na Shopee e retorna URLs"""
    print(f"  [BUSCA] '{termo}'...")
    nav(f"https://shopee.com.br/search?keyword={quote(termo)}")
    time.sleep(8)
    
    result = run_js("""
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.href || '';
            if (href.includes('-i.') && href.includes('shopee.com.br')) {
                // Simplificar URL
                const match = href.match(/(https:\\/\\/shopee\\.com\\.br\\/[^?]+)/);
                if (match) links.push(match[1]);
            }
        });
        JSON.stringify([...new Set(links)].slice(0, """ + str(limit) + """));
    """)
    
    if result:
        try:
            urls = json.loads(result)
            # Extrair nomes dos produtos da URL
            prods = []
            for u in urls:
                name = u.split("/")[-1].split("-i.")[0].replace("-", " ")
                prods.append({"titulo": name[:60], "url": u})
            return prods
        except:
            pass
    return []

def gerar_links_afiliado(urls):
    """Gera links de afiliado via dashboard"""
    print(f"  [LINK] Gerando {len(urls)} links...")
    nav("https://affiliate.shopee.com.br/offer/custom_link")
    time.sleep(6)
    
    # Preencher textarea
    urls_str = "\\n".join(urls)
    r = run_js(f"""
        const ta = document.querySelector('textarea.ant-input');
        if (ta) {{
            ta.focus();
            const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            setter.call(ta, '{urls_str}');
            ta.dispatchEvent(new Event('input', {{bubbles: true}}));
            ta.dispatchEvent(new Event('change', {{bubbles: true}}));
            'OK';
        }} else {{ 'NO_TA'; }}
    """)
    if r != "OK":
        print(f"  [LINK] Textarea não encontrada: {r}")
        return []
    
    time.sleep(1)
    
    # Clicar Obter link
    run_js("""
        const btns = document.querySelectorAll('button');
        for (const btn of btns) {
            if ((btn.textContent || '').includes('Obter link')) {
                btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                break;
            }
        }
        'ok';
    """)
    time.sleep(5)
    
    # Extrair links do modal
    result = run_js("""
        const modal = document.querySelector('.ant-modal');
        if (modal) {
            const inputs = modal.querySelectorAll('input, textarea');
            let links = [];
            inputs.forEach(el => {
                const val = (el.value || '').trim();
                if (val.includes('s.shopee') || val.includes('shp.ee')) {
                    links.push(val);
                }
            });
            // Fallback: get from text
            if (links.length === 0) {
                const text = modal.innerText;
                const matches = text.match(/https:\\/\\/s\\.shopee[^\\s\\n]+/g);
                if (matches) links = matches;
            }
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
    run_js("const c = document.querySelector('.ant-modal-close'); if(c) c.click(); 'ok';")
    time.sleep(1)
    
    return links

def main():
    existing = []
    try:
        with open("affiliate_links.json") as f:
            existing = json.load(f)
    except:
        pass
    
    existing_urls = {l.get("url_original", "") for l in existing}
    novos = 0
    
    termos = TERMOS_LUCRATIVOS[:]
    random.shuffle(termos)
    
    for termo in termos:
        print(f"\n{'='*50}")
        print(f"📦 Termo: {termo}")
        print(f"{'='*50}")
        
        produtos = buscar_links_produto(termo, limit=5)
        if not produtos:
            print(f"  ⚠️ Nenhum produto encontrado")
            continue
        
        # Filtrar duplicados
        novos_prods = [p for p in produtos if p["url"] not in existing_urls]
        if not novos_prods:
            print(f"  ⏭️ Todos já cadastrados")
            continue
        
        urls = [p["url"] for p in novos_prods[:5]]
        aff_links = gerar_links_afiliado(urls)
        
        for i, prod in enumerate(novos_prods[:5]):
            aff = aff_links[i] if i < len(aff_links) else None
            entry = {
                "id": hashlib.md5(prod["url"].encode()).hexdigest()[:8],
                "categoria": termo,
                "titulo": prod["titulo"],
                "url_original": prod["url"],
                "url_afiliado": aff,
                "preco": "",
                "data": datetime.now().isoformat(),
                "postado": False,
            }
            existing.append(entry)
            existing_urls.add(prod["url"])
            novos += 1
            status = "✅" if aff else "❌"
            print(f"  {status} {prod['titulo'][:40]}")
        
        # Salvar após cada lote
        with open("affiliate_links.json", "w") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 Salvos! Total: {len(existing)} ({novos} novos)")
        
        if novos >= 50:
            break
        
        time.sleep(3)
    
    print(f"\n🏁 FINALIZADO! {novos} novos links gerados. Total: {len(existing)}")

if __name__ == "__main__":
    main()
