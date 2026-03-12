#!/usr/bin/env python3
"""
Substitui links de afiliado dos canais Telegram pelos SEUS links de afiliado.

Estratégia dupla:
1. Match local: cruza com affiliate_links.json (links já gerados anteriormente)
2. Chrome: gera novos links via Shopee Affiliate Dashboard (se Chrome disponível)
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
AFFILIATE_FILE = os.path.join(DIR, "affiliate_links.json")


def resolve_shopee_link(short_url):
    """Resolve s.shopee.com.br/XXX -> URL real do produto"""
    if not short_url:
        return None
    if "product-i." in short_url or "-i." in short_url:
        return short_url
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            resp = client.head(short_url)
            final_url = str(resp.url)
            if "shopee.com.br" in final_url:
                return final_url.split("?")[0]
    except:
        pass
    return None


def extract_item_id(url):
    """Extrai item_id da URL do Shopee"""
    if not url:
        return None
    # Pattern: -i.SHOP_ID.ITEM_ID
    m = re.search(r'-i\.(\d+)\.(\d+)', url)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    # Pattern: /SHOP_ID/ITEM_ID
    m = re.search(r'/(\d{6,})/(\d{8,})', url)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    return None


def extract_product_name(url):
    """Extrai nome do produto da URL"""
    if not url:
        return ""
    # Pegar parte antes de -i.
    parts = url.split("/")
    for part in parts:
        if "-i." in part:
            name = part.split("-i.")[0].replace("-", " ")
            return name[:60]
    return ""


def run_js(js):
    """Executa JavaScript no Chrome via AppleScript"""
    escaped = js.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    script = f'tell application "Google Chrome"\n  tell active tab of front window\n    execute javascript "{escaped}"\n  end tell\nend tell'
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else None
    except:
        return None


def nav(url):
    """Navega no Chrome"""
    script = f'tell application "Google Chrome"\n  tell active tab of front window\n    set URL to "{url}"\n  end tell\nend tell'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=15)
        return True
    except:
        return False


def chrome_available():
    """Verifica se Chrome esta aberto"""
    try:
        r = subprocess.run(["osascript", "-e", 'tell application "System Events" to (name of processes) contains "Google Chrome"'],
                          capture_output=True, text=True, timeout=5)
        return "true" in r.stdout.lower()
    except:
        return False


def gerar_link_afiliado_batch(product_urls):
    """Gera links de afiliado via dashboard (batch de ate 5)"""
    if not product_urls or not chrome_available():
        return []

    print(f"  Gerando {len(product_urls)} links de afiliado via Chrome...")
    if not nav("https://affiliate.shopee.com.br/offer/custom_link"):
        return []
    time.sleep(6)

    urls_str = "\\n".join(product_urls)
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
        print(f"  Dashboard nao disponivel: {r}")
        return []

    time.sleep(1)
    run_js("""
        const btns = document.querySelectorAll('button');
        for (const btn of btns) {
            if ((btn.textContent || '').includes('Obter link') || (btn.textContent || '').includes('Get link')) {
                btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                break;
            }
        }
        'ok';
    """)
    time.sleep(5)

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

    run_js("const c = document.querySelector('.ant-modal-close'); if(c) c.click(); 'ok';")
    time.sleep(1)
    return links


def process_pending_affiliates():
    """Processa todos os videos pendentes"""
    pending = json.load(open(PENDING_FILE))

    # Carregar links de afiliado existentes
    existing_aff = []
    try:
        existing_aff = json.load(open(AFFILIATE_FILE))
    except:
        pass

    # Mapear item_ids dos links existentes
    aff_by_item = {}
    for aff in existing_aff:
        url = aff.get("url_original", "")
        link = aff.get("url_afiliado", "")
        if link:
            iid = extract_item_id(url)
            if iid:
                aff_by_item[iid] = link

    print(f"Links de afiliado existentes: {len(aff_by_item)}")

    # Filtrar: so os que tem link do canal mas nao tem nosso
    need_affiliate = [e for e in pending if e.get("shopee_link") and not e.get("my_affiliate_link")]

    if not need_affiliate:
        print("Todos os videos ja tem link de afiliado proprio!")
        return 0

    print(f"Videos precisando de link proprio: {len(need_affiliate)}\n")

    # ETAPA 1: Resolver links curtos
    print("ETAPA 1: Resolvendo links curtos...")
    resolved_cache = {}
    for entry in need_affiliate:
        link = entry.get("shopee_link", "")
        if link in resolved_cache:
            entry["_real_url"] = resolved_cache[link]
            continue
        real_url = resolve_shopee_link(link)
        if real_url:
            resolved_cache[link] = real_url
            entry["_real_url"] = real_url
            print(f"  OK: ...{real_url[-50:]}")
        else:
            entry["_real_url"] = None

    print(f"  Resolvidos: {len(resolved_cache)}\n")

    # ETAPA 2: Match local com affiliate_links.json
    print("ETAPA 2: Match local com links existentes...")
    matched_local = 0
    need_chrome = []

    for entry in need_affiliate:
        real_url = entry.get("_real_url", "")
        if not real_url:
            continue

        iid = extract_item_id(real_url)
        if iid and iid in aff_by_item:
            entry["my_affiliate_link"] = aff_by_item[iid]
            matched_local += 1
            print(f"  Match local: {iid} -> {aff_by_item[iid]}")
        else:
            need_chrome.append(entry)

    print(f"  Match local: {matched_local}")
    print(f"  Precisam Chrome: {len(need_chrome)}\n")

    # ETAPA 3: Gerar via Chrome (se disponivel)
    generated_chrome = 0
    if need_chrome and chrome_available():
        print("ETAPA 3: Gerando via Chrome Affiliate Dashboard...")
        
        # Deduplicar URLs
        url_to_entries = {}
        for entry in need_chrome:
            purl = entry.get("_real_url")
            if purl:
                url_to_entries.setdefault(purl, []).append(entry)

        unique_urls = list(url_to_entries.keys())
        for i in range(0, len(unique_urls), 5):
            batch = unique_urls[i:i+5]
            print(f"\n  Batch {i//5 + 1}: {len(batch)} produtos")
            aff_links = gerar_link_afiliado_batch(batch)

            for j, purl in enumerate(batch):
                aff = aff_links[j] if j < len(aff_links) else None
                if aff:
                    for entry in url_to_entries[purl]:
                        entry["my_affiliate_link"] = aff
                        entry["product_url_real"] = purl
                        generated_chrome += 1
                    
                    # Salvar no affiliate_links.json tambem
                    existing_aff.append({
                        "titulo": extract_product_name(purl),
                        "url_original": purl,
                        "url_afiliado": aff,
                        "data": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "source": "telegram_matcher",
                    })
                    print(f"    Gerado: {aff}")
                else:
                    print(f"    Falha: {purl[:50]}")

            if i + 5 < len(unique_urls):
                time.sleep(3)

        # Salvar affiliate_links.json atualizado
        with open(AFFILIATE_FILE, "w") as f:
            json.dump(existing_aff, f, indent=2, ensure_ascii=False)

    elif need_chrome:
        print("ETAPA 3: Chrome nao disponivel, pulando geracao de novos links")
        print("  Dica: Abra o Chrome e logue em affiliate.shopee.com.br")

    # ETAPA 4: Atualizar descricoes
    print("\nETAPA 4: Atualizando descricoes...")
    updated = 0
    for entry in pending:
        my_link = entry.get("my_affiliate_link", "")
        if my_link and not entry.get("description_updated"):
            text = entry.get("text", "")
            name = text.split("https")[0].split("http")[0].strip()
            name = re.sub(r'Video \d+:', '', name).strip()
            name = name.split("\n")[0][:80].strip()
            if not name or len(name) < 3:
                name = "Achado Incrivel da Shopee"

            entry["clean_description"] = f"{name}\n#shopee #achadosshopee #shopeefinds #promocao\n{my_link}"
            entry["description_updated"] = True
            updated += 1

    # Limpar temp
    for entry in pending:
        entry.pop("_real_url", None)

    # Salvar
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f, indent=2, ensure_ascii=False)

    total = matched_local + generated_chrome
    print(f"\n{'='*60}")
    print(f"  RESULTADO:")
    print(f"  Match local:     {matched_local}")
    print(f"  Gerados Chrome:  {generated_chrome}")
    print(f"  Total com link:  {total}")
    print(f"  Descricoes:      {updated}")
    print(f"{'='*60}\n")
    return total


if __name__ == "__main__":
    process_pending_affiliates()
