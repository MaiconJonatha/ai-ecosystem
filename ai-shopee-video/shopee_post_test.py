#!/usr/bin/env python3
"""Posta produto automaticamente na Shopee Seller Center"""
import asyncio, json, os, glob, random, sys
sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1)

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

async def main():
    from playwright.async_api import async_playwright

    p = await async_playwright().start()
    print("[1] Abrindo Chrome...")

    browser = await p.chromium.launch(
        headless=False, channel="chrome",
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = await browser.new_context(
        viewport={"width": 1280, "height": 900}, locale="pt-BR",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

    with open("shopee_cookies.json") as f:
        cookies = json.load(f)
    await context.add_cookies(cookies)

    page = await context.new_page()

    # Produto a postar
    produto = "Fone Bluetooth TWS Sem Fio Premium"
    preco = "49.90"
    estoque = "999"

    print(f"[2] Produto: {produto}")
    await page.goto("https://seller.shopee.com.br/portal/product/new", timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(8)  # Esperar mais para carregar

    if "inactive" in page.url:
        print("[!] Reativando loja...")
        await page.evaluate('''() => {
            for (const btn of document.querySelectorAll('button')) {
                if (btn.textContent.includes("Reativar")) { btn.click(); return; }
            }
        }''')
        await asyncio.sleep(5)
        await page.goto("https://seller.shopee.com.br/portal/product/new", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(8)

    # === UPLOAD IMAGEM ===
    file_inputs = page.locator('input[type="file"]')
    count = await file_inputs.count()
    print(f"[3] Upload areas: {count}")

    # Esperar até ter file inputs
    if count == 0:
        print("[3] Aguardando carregar...")
        try:
            await page.wait_for_selector('input[type="file"]', timeout=10000)
            count = await file_inputs.count()
            print(f"[3] Agora: {count} inputs")
        except:
            print("[3] Sem inputs de upload, tentando scroll...")
            await page.evaluate("window.scrollBy(0, 300)")
            await asyncio.sleep(3)
            count = await file_inputs.count()

    imgs = sorted(glob.glob("static/images/prod_*.*"), key=os.path.getmtime, reverse=True)
    imgs = [f for f in imgs if os.path.getsize(f) > 1000]

    if imgs and count > 0:
        img = imgs[0]
        # Upload no primeiro file input (imagem)
        for i in range(count):
            accept = await file_inputs.nth(i).get_attribute("accept") or ""
            if "image" in accept or i == 0:
                await file_inputs.nth(i).set_input_files(img)
                print(f"[3] Imagem OK: {os.path.basename(img)}")
                await asyncio.sleep(3)
                break

    # === NOME DO PRODUTO ===
    r = await page.evaluate('''(nome) => {
        const inp = document.querySelector('input[placeholder*="Nome da Marca"]');
        if (!inp) return "NOT FOUND";
        inp.focus();
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(inp, nome);
        inp.dispatchEvent(new Event('input', {bubbles: true}));
        inp.dispatchEvent(new Event('change', {bubbles: true}));
        inp.dispatchEvent(new Event('blur', {bubbles: true}));
        return "OK: " + inp.value.substring(0, 30);
    }''', produto)
    print(f"[4] Nome: {r}")
    await asyncio.sleep(2)

    # === DESCRIÇÃO ===
    desc = f"""🔥 {produto} - MELHOR PREÇO DA SHOPEE!

✅ Bluetooth 5.3 - Conexão ultra estável
✅ Cancelamento de ruído ativo (ANC)
✅ 30h de bateria com estojo de carregamento
✅ Resistente à água IPX5
✅ Driver de 13mm com som Hi-Fi

📦 Envio IMEDIATO após pagamento!
🚚 FRETE GRÁTIS para todo Brasil!
⭐ Satisfação garantida ou dinheiro de volta!

#fone #bluetooth #tws #achadinhos #shopee"""

    desc_area = page.locator('textarea, [contenteditable="true"]:not([role="textbox"])')
    if await desc_area.count() > 0:
        await desc_area.first.click()
        await asyncio.sleep(0.3)
        await desc_area.first.fill(desc)
        print("[5] Descrição preenchida!")
    await asyncio.sleep(1)

    # === SCROLL PARA PREÇO ===
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.6)")
    await asyncio.sleep(2)

    # === PREÇO ===
    price_filled = await page.evaluate(f'''() => {{
        const inputs = document.querySelectorAll('input');
        for (const inp of inputs) {{
            const ph = (inp.placeholder || '').toLowerCase();
            if (ph.includes('inserir') || ph.includes('preço') || ph.includes('price')) {{
                inp.focus();
                document.execCommand('selectAll');
                document.execCommand('insertText', false, "{preco}");
                return "OK: " + ph;
            }}
        }}
        return "FAIL";
    }}''')
    print(f"[6] Preço: {price_filled}")

    # === ESTOQUE ===
    stock_filled = await page.evaluate(f'''() => {{
        const inputs = document.querySelectorAll('input');
        for (const inp of inputs) {{
            const ph = (inp.placeholder || '').toLowerCase();
            if (ph.includes('inserir') && inp !== document.activeElement) {{
                inp.focus();
                document.execCommand('selectAll');
                document.execCommand('insertText', false, "{estoque}");
                return "OK: " + ph;
            }}
        }}
        return "FAIL";
    }}''')
    print(f"[7] Estoque: {stock_filled}")

    # === SCROLL AO FINAL ===
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(2)

    # === SALVAR E PUBLICAR ===
    print("[8] Procurando botão de publicar...")
    buttons = await page.evaluate('''() => {
        const btns = [];
        document.querySelectorAll('button').forEach(b => {
            const t = b.textContent.trim();
            if (t.length < 40 && t.length > 0) btns.push(t);
        });
        return btns;
    }''')
    print(f"    Botões: {buttons}")

    # Clicar em "Salvar" (primeiro botão de salvar disponível)
    pub = await page.evaluate('''() => {
        const btns = document.querySelectorAll('button');
        for (const btn of btns) {
            const t = btn.textContent.trim();
            if (t === 'Salvar' && btn.offsetParent !== null) {
                btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                return "CLICKED: Salvar";
            }
        }
        // Tentar Next Step se não tiver Salvar
        for (const btn of btns) {
            const t = btn.textContent.trim();
            if (t === 'Next Step' && btn.offsetParent !== null) {
                btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                return "CLICKED: Next Step";
            }
        }
        return "NOT FOUND";
    }''')
    print(f"[8] Ação: {pub}")
    await asyncio.sleep(5)

    # Verificar se apareceu erro ou confirmação
    errors = await page.evaluate('''() => {
        const errors = [];
        document.querySelectorAll('[class*="error"], [class*="warning"], [class*="toast"], [class*="alert"]').forEach(el => {
            const t = el.textContent?.trim();
            if (t && t.length < 200) errors.push(t);
        });
        return errors;
    }''')
    if errors:
        print(f"[8] Erros/avisos: {errors[:3]}")

    # Se tem Confirmar, clicar
    conf = await page.evaluate('''() => {
        const btns = document.querySelectorAll('button');
        for (const btn of btns) {
            const t = btn.textContent.trim();
            if (t === 'Confirmar' && btn.offsetParent !== null) {
                btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                return "CLICKED: Confirmar";
            }
        }
        return "no confirm";
    }''')
    if "CLICKED" in conf:
        print(f"[8] {conf}")
    await asyncio.sleep(5)

    # Agora tentar Salvar (o botão final de publicar)
    print("[9] Tentando Salvar produto...")
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(2)

    save = await page.evaluate('''() => {
        const btns = document.querySelectorAll('button');
        // Procurar o último botão "Salvar" (geralmente é o de publicar)
        let lastSave = null;
        for (const btn of btns) {
            const t = btn.textContent.trim();
            if (t === 'Salvar' && btn.offsetParent !== null) {
                lastSave = btn;
            }
        }
        if (lastSave) {
            lastSave.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            return "CLICKED: Salvar (último)";
        }
        return "NOT FOUND";
    }''')
    print(f"[9] {save}")
    await asyncio.sleep(8)

    # Checar se salvou ou tem erros
    errors2 = await page.evaluate('''() => {
        const errors = [];
        document.querySelectorAll('[class*="error"], [class*="warning"], [class*="toast"], [class*="msg"]').forEach(el => {
            const t = el.textContent?.trim();
            if (t && t.length > 5 && t.length < 200) errors.push(t);
        });
        // Também checar textos vermelhos
        document.querySelectorAll('span, div').forEach(el => {
            const style = getComputedStyle(el);
            if (style.color === 'rgb(255, 0, 0)' || style.color === 'red') {
                const t = el.textContent?.trim();
                if (t && t.length > 3 && t.length < 100) errors.push("RED: " + t);
            }
        });
        return errors.slice(0, 10);
    }''')
    if errors2:
        print(f"[9] Mensagens: {errors2[:5]}")

    # Check resultado
    print(f"[9] URL final: {page.url}")
    text = await page.evaluate("document.body?.innerText?.substring(0, 200) || ''")
    print(f"[9] Conteúdo: {text[:150]}")

    cookies = await context.cookies()
    with open("shopee_cookies.json", "w") as f:
        json.dump(cookies, f)

    await asyncio.sleep(10)
    await browser.close()
    await p.stop()
    print("[DONE]")

asyncio.run(main())
