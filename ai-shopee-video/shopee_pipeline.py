#!/usr/bin/env python3
"""
Shopee Video Pipeline - Post videos to Shopee Video Creator Center
Used by telegram_shopee.py for auto-posting
"""
import asyncio, json, os

DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES = os.path.join(DIR, "shopee_cookies.json")

async def post_to_shopee_video(video_path, description):
    """Upload e posta um vídeo no Shopee Video"""
    from playwright.async_api import async_playwright
    
    if not os.path.exists(video_path):
        print(f"[SHOPEE] Video não encontrado: {video_path}")
        return False
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(
        headless=False, channel="chrome",
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = await browser.new_context(
        viewport={"width": 1280, "height": 900}, locale="pt-BR",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    )
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
    
    if os.path.exists(COOKIES):
        await context.add_cookies(json.load(open(COOKIES)))
    
    page = await context.new_page()
    success = False
    
    try:
        await page.goto("https://seller.shopee.com.br/creator-center/video-upload/upload", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(15)
        
        if "login" in page.url.lower():
            print("[SHOPEE] Sessão expirada!")
            await browser.close()
            await p.stop()
            return False
        
        # Upload
        fi = page.locator('input[type="file"]')
        if await fi.count() == 0:
            await page.reload()
            await asyncio.sleep(15)
            fi = page.locator('input[type="file"]')
        
        if await fi.count() == 0:
            print("[SHOPEE] Sem file input")
            await browser.close()
            await p.stop()
            return False
        
        await fi.first.set_input_files(video_path)
        
        # Esperar upload
        for i in range(40):
            await asyncio.sleep(2)
            try:
                text = await page.evaluate("(document.body.innerText||'')")
                if "Enviado" in text:
                    break
            except: pass
        
        await asyncio.sleep(5)
        
        # Legenda
        legenda = page.locator('[contenteditable="true"]').first
        if await legenda.count() > 0:
            await legenda.click()
            await legenda.fill(description[:150])  # Shopee limita a 150 chars
        
        await asyncio.sleep(2)
        
        # Checkbox termos
        await page.evaluate("""() => {
            var cb = document.querySelector('input[type=checkbox]');
            if (!cb) return;
            var wrapper = cb.closest('[class*=checkbox]') || cb.parentElement;
            if (wrapper) wrapper.click();
        }""")
        await asyncio.sleep(1)
        
        checked = await page.evaluate("document.querySelector('input[type=checkbox]')?.checked || false")
        if not checked:
            await page.evaluate("var cb=document.querySelector('input[type=checkbox]'); if(cb) cb.parentElement.click();")
            await asyncio.sleep(1)
        
        # Publicar
        pub = page.locator('button:has-text("Publicar")')
        if await pub.count() > 0:
            await pub.first.click()
            await asyncio.sleep(10)
            text = await page.evaluate("(document.body.innerText||'').substring(0,500)")
            success = "sucesso" in text.lower() or "manage" in page.url
        
        # Salvar cookies
        json.dump(await context.cookies(), open(COOKIES, "w"))
        
    except Exception as e:
        print(f"[SHOPEE] Erro: {e}")
    
    await browser.close()
    await p.stop()
    return success
