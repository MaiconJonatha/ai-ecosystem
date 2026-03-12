#!/usr/bin/env python3
"""
Passo 1: Login no YouTube - salva perfil do Firefox para uso posterior.
Executa o Firefox com perfil persistente. Faça login manual no Google/YouTube.
Feche o navegador quando terminar (o perfil fica salvo).
"""

import asyncio
from playwright.async_api import async_playwright
import os

PROFILE_DIR = os.path.join(os.path.dirname(__file__), "youtube_firefox_profile")

async def main():
    print("[*] Abrindo Firefox para login no YouTube...")
    print(f"[*] Perfil será salvo em: {PROFILE_DIR}")
    print("[*] Faça login na sua conta Google/YouTube.")
    print("[*] Depois feche o navegador normalmente (Cmd+Q ou X).")
    print()
    
    async with async_playwright() as p:
        browser = await p.firefox.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            viewport={"width": 1280, "height": 900},
            locale="pt-BR",
            slow_mo=100,
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await page.goto("https://studio.youtube.com", wait_until="networkidle", timeout=60000)
        
        print("[*] Navegador aberto. Faça login e depois FECHE o navegador.")
        
        # Aguardar até o navegador ser fechado pelo usuário
        try:
            await page.wait_for_event("close", timeout=600000)  # 10 min
        except:
            pass
        
        try:
            await browser.close()
        except:
            pass
    
    print("[+] Perfil salvo! Agora execute youtube_upload.py para postar o vídeo.")

if __name__ == "__main__":
    asyncio.run(main())
