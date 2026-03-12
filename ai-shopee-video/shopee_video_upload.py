#!/usr/bin/env python3
"""
Upload de vídeos no Shopee Creator Center (Live & Video)
Usa Playwright com Chrome real para evitar detecção anti-bot
"""
import asyncio, json, os, sys, glob, time
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

    # Carregar cookies se existirem
    if os.path.exists("shopee_cookies.json"):
        with open("shopee_cookies.json") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        print("[1] Cookies carregados")

    page = await context.new_page()

    # Verificar login
    await page.goto("https://seller.shopee.com.br/", timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(5)

    if "login" in page.url.lower():
        print("[!] Precisa fazer login manualmente...")
        print("[!] Faça login no navegador que abriu")
        for i in range(60):
            await asyncio.sleep(5)
            if "login" not in page.url.lower():
                print("[✓] Login detectado!")
                break
            if i % 6 == 0:
                print(f"[!] Aguardando login... {i*5}s")
    
    # Salvar cookies
    cookies = await context.cookies()
    with open("shopee_cookies.json", "w") as f:
        json.dump(cookies, f)
    print("[2] Cookies salvos")

    # Navegar para Creator Center > Vídeo
    print("[3] Navegando para Creator Center > Vídeo...")
    await page.goto("https://seller.shopee.com.br/creator-center/insight/video", timeout=60000, wait_until="domcontentloaded")
    await asyncio.sleep(10)

    # Esperar conteúdo carregar
    print("[3] Esperando conteúdo carregar...")
    await asyncio.sleep(10)

    # Procurar botões de Enviar Vídeo / Gerenciar Vídeo
    page_text = await page.evaluate("document.body.innerText.substring(0, 5000)")
    print(f"[3] Texto da página: {page_text[:500]}")

    # Procurar botão Enviar Vídeo
    enviar_btn = await page.evaluate("""() => {
        const els = document.querySelectorAll('a, button, div, span');
        for (const el of els) {
            const t = (el.textContent || '').trim();
            if (t === 'Enviar Vídeo' || t === 'Upload Video') {
                return {text: t, tag: el.tagName, href: el.getAttribute('href') || ''};
            }
        }
        return null;
    }""")
    print(f"[4] Botão Enviar: {enviar_btn}")

    # Se encontrou, clicar
    if enviar_btn:
        await page.evaluate("""() => {
            const els = document.querySelectorAll('a, button, div, span');
            for (const el of els) {
                const t = (el.textContent || '').trim();
                if (t === 'Enviar Vídeo' || t === 'Upload Video') {
                    el.click();
                    return true;
                }
            }
            return false;
        }""")
        await asyncio.sleep(5)
        print(f"[4] URL após click: {page.url}")

    # Buscar file inputs para upload
    file_inputs = page.locator('input[type="file"]')
    count = await file_inputs.count()
    print(f"[5] File inputs: {count}")

    if count == 0:
        # Tentar esperar
        try:
            await page.wait_for_selector('input[type="file"]', timeout=15000)
            count = await file_inputs.count()
            print(f"[5] File inputs (after wait): {count}")
        except:
            print("[5] Nenhum input de upload encontrado")

    # Se tiver upload, fazer upload do vídeo
    if count > 0:
        # Pegar vídeos disponíveis
        videos = sorted(glob.glob("static/videos/*.mp4") + glob.glob("videos/*.mp4"), 
                       key=os.path.getmtime, reverse=True)
        if videos:
            video = videos[0]
            print(f"[6] Fazendo upload: {os.path.basename(video)}")
            for i in range(count):
                accept = await file_inputs.nth(i).get_attribute("accept") or ""
                if "video" in accept or i == 0:
                    await file_inputs.nth(i).set_input_files(video)
                    print(f"[6] Upload iniciado!")
                    await asyncio.sleep(30)  # Esperar upload
                    break
        else:
            print("[6] Nenhum vídeo disponível para upload")

    # Checar página atual
    all_text = await page.evaluate("document.body.innerText.substring(0, 3000)")
    print(f"\n[INFO] Conteúdo da página:")
    print(all_text[:1000])

    # Listar todos os links disponíveis no creator center
    links = await page.evaluate("""() => {
        const links = [];
        document.querySelectorAll('a[href]').forEach(a => {
            const t = a.textContent.trim();
            const h = a.getAttribute('href');
            if (t.length > 0 && t.length < 50 && (h.includes('creator') || h.includes('video') || h.includes('upload'))) {
                links.push(t + ' -> ' + h);
            }
        });
        return links;
    }""")
    print(f"\n[LINKS] Relacionados a vídeo:")
    for l in links:
        print(f"  {l}")

    # Manter browser aberto
    print("\n[OK] Browser aberto. Pressione Ctrl+C para fechar.")
    try:
        while True:
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        pass

    cookies = await context.cookies()
    with open("shopee_cookies.json", "w") as f:
        json.dump(cookies, f)
    
    await browser.close()
    await p.stop()
    print("[DONE]")

asyncio.run(main())
