#!/usr/bin/env python3
"""
Define thumbnail nos vídeos mais recentes do YouTube Studio.
Usa Firefox com perfil persistente (já logado).
"""

import asyncio
import os
import sys
from playwright.async_api import async_playwright

PROFILE_DIR = os.path.join(os.path.dirname(__file__), "youtube_firefox_profile")
THUMBNAIL_PATH = sys.argv[1] if len(sys.argv) > 1 else "/Users/maiconjonathamartinsdasilva/Downloads/Jesus_christ_standing_on_a_mountain_top_surrounded_delpmaspu.png"
MAX_VIDEOS = int(sys.argv[2]) if len(sys.argv) > 2 else 5

async def main():
    print(f"[*] Thumbnail: {THUMBNAIL_PATH}")
    print(f"[*] Max videos: {MAX_VIDEOS}")
    
    if not os.path.exists(THUMBNAIL_PATH):
        print(f"[!] Thumbnail nao encontrada: {THUMBNAIL_PATH}")
        return
    
    async with async_playwright() as p:
        browser = await p.firefox.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            viewport={"width": 1400, "height": 900},
            locale="pt-BR",
            slow_mo=200,
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        # Ir para YouTube Studio - Content
        print("[*] Abrindo YouTube Studio > Content...")
        await page.goto("https://studio.youtube.com/channel/UC/videos/upload", wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)
        
        # Redireciona para a URL correta do canal
        url = page.url
        print(f"[*] URL: {url}")
        
        if "studio.youtube.com" not in url:
            print("[!] Nao esta no YouTube Studio. Tentando direto...")
            await page.goto("https://studio.youtube.com", wait_until="networkidle", timeout=60000)
            await asyncio.sleep(5)
            url = page.url
            print(f"[*] URL: {url}")
        
        # Clicar em "Content" no menu lateral se necessário
        try:
            content_link = page.locator('a[href*="/videos"], #menu-item-1')
            if await content_link.count() > 0:
                await content_link.first.click()
                await asyncio.sleep(3)
        except:
            pass
        
        print("[*] Procurando videos...")
        
        # Encontrar linhas de vídeos na tabela
        video_rows = page.locator('ytcp-video-row, tr.video-row, a[href*="/video/"]')
        count = await video_rows.count()
        print(f"[*] Encontrados {count} elementos de video")
        
        if count == 0:
            # Tentar outro seletor
            video_rows = page.locator('#video-title')
            count = await video_rows.count()
            print(f"[*] Tentativa 2: {count} titulos de video")
        
        if count == 0:
            print("[!] Nenhum video encontrado. Tirando screenshot...")
            await page.screenshot(path="/tmp/yt_studio_debug.png")
            print("[*] Screenshot salvo em /tmp/yt_studio_debug.png")
            print("[*] Aguardando 60s para debug manual...")
            await asyncio.sleep(60)
            await browser.close()
            return
        
        videos_done = 0
        
        for i in range(min(count, MAX_VIDEOS)):
            try:
                print(f"\n[*] --- Video {i+1} ---")
                
                # Clicar no vídeo para abrir editor
                video_rows = page.locator('#video-title')
                title_text = await video_rows.nth(i).text_content()
                print(f"[*] Video: {title_text.strip()[:60] if title_text else 'sem titulo'}")
                
                await video_rows.nth(i).click()
                await asyncio.sleep(4)
                
                # Procurar botão de thumbnail/upload thumbnail
                # YouTube Studio tem um botão "Upload thumbnail" ou "Enviar miniatura"
                thumb_btn = page.locator('button:has-text("thumbnail"), button:has-text("miniatura"), button:has-text("Upload"), #still-picker button, .thumbnail-editor button')
                
                if await thumb_btn.count() == 0:
                    # Tentar input file diretamente
                    file_input = page.locator('input[type="file"][accept*="image"]')
                    if await file_input.count() > 0:
                        await file_input.first.set_input_files(THUMBNAIL_PATH)
                        print(f"[+] Thumbnail enviada via input file!")
                        await asyncio.sleep(3)
                    else:
                        # Procurar qualquer input file
                        all_inputs = page.locator('input[type="file"]')
                        input_count = await all_inputs.count()
                        print(f"[*] Inputs file encontrados: {input_count}")
                        
                        if input_count > 0:
                            await all_inputs.first.set_input_files(THUMBNAIL_PATH)
                            print(f"[+] Thumbnail enviada!")
                            await asyncio.sleep(3)
                        else:
                            print("[!] Nenhum input de upload encontrado. Screenshot...")
                            await page.screenshot(path=f"/tmp/yt_video_{i}_debug.png")
                else:
                    await thumb_btn.first.click()
                    await asyncio.sleep(2)
                    
                    # Depois de clicar, procurar input file
                    file_input = page.locator('input[type="file"]')
                    if await file_input.count() > 0:
                        await file_input.first.set_input_files(THUMBNAIL_PATH)
                        print(f"[+] Thumbnail enviada!")
                        await asyncio.sleep(3)
                
                # Salvar - clicar no botão SAVE
                save_btn = page.locator('#save-button, button:has-text("Salvar"), button:has-text("Save")')
                if await save_btn.count() > 0:
                    # Verificar se está habilitado
                    is_disabled = await save_btn.first.get_attribute("aria-disabled")
                    if is_disabled != "true":
                        await save_btn.first.click()
                        print("[+] SALVO!")
                        await asyncio.sleep(3)
                    else:
                        print("[*] Botão Save desabilitado (sem mudanças?)")
                
                videos_done += 1
                
                # Voltar para lista de vídeos
                await page.go_back()
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"[!] Erro no video {i+1}: {e}")
                # Tentar voltar
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(3)
                except:
                    pass
        
        print(f"\n{'='*60}")
        print(f"[+] Thumbnail atualizada em {videos_done} videos!")
        print(f"{'='*60}")
        
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
