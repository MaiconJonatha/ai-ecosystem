import asyncio, json, os, subprocess, time, urllib.request, shutil, signal

BASE = "/Users/maiconjonathamartinsdasilva/a-criacao-de-ruma-redessocial.de-ia./ai-shopee-video"
PENDING = os.path.join(BASE, "telegram_pending.json")
COOKIES = os.path.join(BASE, "shopee_cookies.json")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE = "/tmp/chrome-sp3"

chrome_proc = None

def start_chrome():
    global chrome_proc
    # Kill any existing chrome with this profile
    subprocess.run(["pkill", "-9", "-f", "chrome-sp3"], capture_output=True)
    time.sleep(2)
    shutil.rmtree(PROFILE, ignore_errors=True)
    os.makedirs(PROFILE, exist_ok=True)
    chrome_proc = subprocess.Popen(
        [CHROME, "--remote-debugging-port=9222",
         "--user-data-dir=" + PROFILE, "--no-first-run"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Chrome PID {chrome_proc.pid}")
    for _ in range(20):
        time.sleep(2)
        try:
            urllib.request.urlopen("http://localhost:9222/json/version")
            print("Chrome ready!")
            return True
        except Exception:
            pass
    print("Chrome failed!")
    return False

def mark_posted(video_path):
    """Atomically mark a video as posted in the JSON"""
    with open(PENDING) as f:
        data = json.load(f)
    for item in data:
        if item.get("video_path") == video_path:
            item["posted_to_shopee"] = True
    with open(PENDING, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_pending():
    """Get list of videos still pending"""
    with open(PENDING) as f:
        data = json.load(f)
    return [v for v in data
            if v.get("shopee_link") and not v.get("posted_to_shopee")
            and os.path.exists(v.get("video_path", ""))]

async def upload_one(page, v):
    """Upload a single video. Returns True on success."""
    await page.goto(
        "https://seller.shopee.com.br/creator-center/video-upload/upload",
        timeout=60000)
    await asyncio.sleep(15)
    fi = page.locator("input[type=file]")
    if await fi.count() == 0:
        print("  No file input")
        return False
    await fi.first.set_input_files(v["video_path"])
    print("  Uploading...")
    for _ in range(60):
        txt = await page.evaluate("document.body.innerText")
        if "Enviado" in txt:
            print("  Upload done!")
            break
        await asyncio.sleep(2)
    await asyncio.sleep(3)
    desc = (v.get("text", "")[:80] if v.get("text") else "Oferta!")
    desc += "\n\n" + v["shopee_link"]
    desc += "\n\n#shopee #oferta #desconto"
    desc = desc[:150]
    leg = page.locator("[contenteditable=true]")
    if await leg.count() > 0:
        await leg.first.click()
        await leg.first.fill(desc)
    await asyncio.sleep(1)
    await page.evaluate(
        "()=>{var cb=document.querySelector('input[type=checkbox]');"
        "if(!cb)return;"
        "var w=cb.closest('[class*=checkbox]')||cb.parentElement;"
        "if(w)w.click();}")
    await asyncio.sleep(1)
    pub = page.locator('button:has-text("Publicar")')
    if await pub.count() > 0:
        await pub.first.click()
        await asyncio.sleep(5)
    return True

async def main():
    from playwright.async_api import async_playwright

    with open(COOKIES) as f:
        cookies = json.load(f)

    to_post = get_pending()[:15]
    print(f"Posting {len(to_post)} videos...")
    if not to_post:
        print("Nothing to post!")
        return

    posted = 0

    async with async_playwright() as p:
        for i, v in enumerate(to_post):
            # Re-check if already posted (by another process)
            fresh_pending = get_pending()
            vid_path = v["video_path"]
            still_pending = any(fp["video_path"] == vid_path for fp in fresh_pending)
            if not still_pending:
                print(f"[{i+1}/{len(to_post)}] Already posted, skip")
                continue

            # Ensure Chrome is running
            try:
                urllib.request.urlopen("http://localhost:9222/json/version")
            except Exception:
                print("  Chrome not running, restarting...")
                if not start_chrome():
                    print("  Failed to restart Chrome!")
                    break

            try:
                print(f"\n[{i+1}/{len(to_post)}] {os.path.basename(vid_path)}")
                browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                ctx = browser.contexts[0]
                await ctx.add_cookies(cookies)
                page = await ctx.new_page()

                ok = await upload_one(page, v)
                if ok:
                    mark_posted(vid_path)
                    posted += 1
                    print("  OK!")

                try:
                    await page.close()
                except Exception:
                    pass

                await asyncio.sleep(30)

            except Exception as e:
                print(f"  Error: {e}")
                # Restart Chrome for next attempt
                subprocess.run(["pkill", "-9", "-f", "chrome-sp3"], capture_output=True)
                await asyncio.sleep(5)
                if not start_chrome():
                    break

    print(f"\nDone! {posted}/{len(to_post)}")
    subprocess.run(["pkill", "-9", "-f", "chrome-sp3"], capture_output=True)

if not start_chrome():
    exit(1)
asyncio.run(main())
