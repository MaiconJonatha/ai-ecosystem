from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import asyncio
import json
import os
import uuid
import time
from datetime import datetime
from pathlib import Path

app = FastAPI(title="AI Image Store - Imagens IA para Venda")

BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "app" / "static" / "images"
PREVIEWS_DIR = BASE_DIR / "app" / "static" / "previews"
DATA_DIR = BASE_DIR / "data"
CATALOG_FILE = DATA_DIR / "catalog.json"
SALES_FILE = DATA_DIR / "sales.json"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

# ===================== IMAGE PROVIDERS =====================
STABLE_HORDE_URL = "https://stablehorde.net/api/v2"
SILICONFLOW_URL = "https://api.siliconflow.com/v1/images/generations"
SILICONFLOW_KEY = os.getenv("SILICONFLOW_KEY", "")
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"

# ===================== CATEGORIES =====================
CATEGORIES = {
    "wallpapers": {
        "name": "Wallpapers 4K",
        "description": "Papeis de parede em alta resolucao para desktop e mobile",
        "price": 2.99,
        "sizes": ["1920x1080", "2560x1440", "3840x2160"],
        "prompts_base": [
            "breathtaking cosmic nebula, stars, deep space, 4k wallpaper, ultra detailed",
            "serene japanese garden with cherry blossoms, zen, peaceful, 4k wallpaper",
            "futuristic cyberpunk city at night, neon lights, rain, 4k wallpaper",
            "majestic mountain landscape at sunset, golden hour, 4k wallpaper",
            "underwater coral reef with tropical fish, crystal clear water, 4k",
            "enchanted forest with bioluminescent mushrooms, magical, fantasy, 4k",
            "aurora borealis over snowy mountains, northern lights, 4k wallpaper",
            "abstract geometric art, vibrant colors, modern design, 4k wallpaper",
            "tropical beach paradise, turquoise water, palm trees, sunset, 4k",
            "vintage retro synthwave landscape, neon grid, sunset, 80s aesthetic, 4k",
        ]
    },
    "banners": {
        "name": "Banners & Headers",
        "description": "Banners profissionais para YouTube, Twitter, LinkedIn, websites",
        "price": 4.99,
        "sizes": ["2560x1440", "1500x500", "1584x396"],
        "prompts_base": [
            "professional tech company banner, modern gradient, minimalist, clean",
            "gaming channel banner, epic fantasy scene, dramatic lighting",
            "creative portfolio banner, abstract art, colorful splashes",
            "fitness and health banner, energetic, vibrant colors, motivational",
            "music studio banner, audio waves, neon lights, dark background",
            "food blog banner, gourmet dishes, warm tones, appetizing",
            "travel blog banner, world landmarks montage, adventure theme",
            "business professional banner, corporate blue, elegant, modern",
            "nature photography banner, stunning landscape, earth tones",
            "education and learning banner, books, knowledge, bright colors",
        ]
    },
    "social_media": {
        "name": "Social Media Posts",
        "description": "Templates visuais para Instagram, Facebook, TikTok",
        "price": 1.99,
        "sizes": ["1080x1080", "1080x1350", "1080x1920"],
        "prompts_base": [
            "motivational quote background, sunrise, inspiring, warm colors",
            "product showcase template, minimalist, elegant, white background",
            "sale promotion background, bold colors, dynamic, eye-catching",
            "holiday celebration background, festive, sparkles, joy",
            "fashion lifestyle aesthetic, soft tones, trendy, instagram worthy",
            "tech product launch, futuristic, sleek, dark theme with glow",
            "wellness and mindfulness, calm, zen, pastel colors, peaceful",
            "sports and fitness motivation, intense, powerful, dark contrast",
            "food photography background, rustic table, warm lighting",
            "pet lovers theme, cute, playful, colorful, happy vibes",
        ]
    },
    "logos": {
        "name": "Logo Concepts",
        "description": "Conceitos de logos e icones para marcas",
        "price": 9.99,
        "sizes": ["1024x1024", "512x512"],
        "prompts_base": [
            "minimalist tech startup logo, geometric, modern, clean white background",
            "vintage coffee shop logo, retro style, warm colors, hand drawn feel",
            "fitness gym logo, strong, bold, dynamic, professional",
            "organic food brand logo, natural, green, leaf elements, fresh",
            "gaming esports logo, fierce, bold colors, competitive",
            "luxury fashion brand logo, elegant, gold, sophisticated, minimal",
            "music studio logo, audio wave, creative, modern, vibrant",
            "pet care brand logo, friendly, cute animal, warm colors",
            "photography studio logo, camera lens, artistic, creative",
            "real estate company logo, building, professional, blue tones",
        ]
    },
    "digital_art": {
        "name": "Arte Digital",
        "description": "Arte digital premium para decoracao e impressao",
        "price": 7.99,
        "sizes": ["2048x2048", "3000x2000"],
        "prompts_base": [
            "surreal dreamscape painting, floating islands, fantasy art, detailed",
            "portrait of a cyberpunk samurai, neon lights, rain, cinematic",
            "steampunk airship over victorian city, detailed illustration, epic",
            "mystical dragon perched on crystal mountain, fantasy digital painting",
            "astronaut floating in space surrounded by colorful planets, sci-fi art",
            "ancient temple ruins in jungle, moss covered, atmospheric, detailed",
            "robot and butterfly in garden, peaceful coexistence, digital painting",
            "underwater city of atlantis, bioluminescent, magical, detailed art",
            "phoenix rising from flames, powerful, majestic, fantasy art",
            "time traveler in a clock dimension, surreal, mind-bending, detailed",
        ]
    },
    "textures": {
        "name": "Texturas & Patterns",
        "description": "Texturas seamless para design grafico e 3D",
        "price": 3.99,
        "sizes": ["1024x1024", "2048x2048"],
        "prompts_base": [
            "seamless marble texture, white and gold veins, luxury, 4k",
            "seamless wood planks texture, oak, natural grain, detailed",
            "seamless abstract geometric pattern, modern, colorful, tileable",
            "seamless brick wall texture, red bricks, weathered, realistic",
            "seamless floral pattern, botanical illustration, vintage style",
            "seamless metal texture, brushed steel, industrial, detailed",
            "seamless watercolor wash texture, soft pastel colors, artistic",
            "seamless tropical leaves pattern, green, lush, botanical",
            "seamless concrete texture, grunge, urban, weathered, grey",
            "seamless galaxy space texture, stars, nebula, cosmic, dark",
        ]
    }
}

def load_catalog():
    if CATALOG_FILE.exists():
        return json.loads(CATALOG_FILE.read_text())
    return {"images": [], "stats": {"total": 0, "total_sales": 0, "revenue": 0.0}}

def save_catalog(catalog):
    CATALOG_FILE.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))

def load_sales():
    if SALES_FILE.exists():
        return json.loads(SALES_FILE.read_text())
    return []

# ===================== IMAGE GENERATION =====================
async def generate_image_stable_horde(prompt: str, width: int = 1024, height: int = 1024):
    """Generate via Stable Horde (free)"""
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            payload = {
                "prompt": prompt + ", masterpiece, best quality, highly detailed",
                "params": {
                    "width": min(width, 1024),
                    "height": min(height, 1024),
                    "steps": 30,
                    "cfg_scale": 7.5,
                    "sampler_name": "k_euler_a"
                },
                "nsfw": False,
                "models": ["stable_diffusion"],
                "r2": True
            }
            resp = await client.post(f"{STABLE_HORDE_URL}/generate/async",
                json=payload, headers={"apikey": "0000000000"})
            if resp.status_code != 202:
                return None
            job_id = resp.json().get("id")
            for _ in range(60):
                await asyncio.sleep(5)
                check = await client.get(f"{STABLE_HORDE_URL}/generate/check/{job_id}")
                if check.json().get("done"):
                    result = await client.get(f"{STABLE_HORDE_URL}/generate/status/{job_id}")
                    gens = result.json().get("generations", [])
                    if gens and gens[0].get("img"):
                        img_url = gens[0]["img"]
                        img_resp = await client.get(img_url)
                        if img_resp.status_code == 200:
                            return img_resp.content
                    break
    except Exception as e:
        print(f"[StableHorde] Error: {e}")
    return None

async def generate_image_pollinations(prompt: str, width: int = 1024, height: int = 1024):
    """Generate via Pollinations (free)"""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            url = f"{POLLINATIONS_URL}/{prompt}?width={width}&height={height}&nologo=true&enhance=true"
            resp = await client.get(url)
            if resp.status_code == 200 and len(resp.content) > 5000:
                return resp.content
    except Exception as e:
        print(f"[Pollinations] Error: {e}")
    return None

async def generate_image_siliconflow(prompt: str, width: int = 1024, height: int = 1024):
    """Generate via SiliconFlow"""
    if not SILICONFLOW_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(SILICONFLOW_URL,
                json={"model": "stabilityai/stable-diffusion-3-5-large",
                      "prompt": prompt, "image_size": f"{width}x{height}"},
                headers={"Authorization": f"Bearer {SILICONFLOW_KEY}"})
            if resp.status_code == 200:
                data = resp.json()
                images = data.get("images", [])
                if images:
                    img_url = images[0].get("url", "")
                    if img_url:
                        img_resp = await client.get(img_url)
                        if img_resp.status_code == 200:
                            return img_resp.content
    except Exception as e:
        print(f"[SiliconFlow] Error: {e}")
    return None

async def generate_image(prompt: str, width: int = 1024, height: int = 1024):
    """Try multiple providers"""
    for provider in [generate_image_pollinations, generate_image_stable_horde, generate_image_siliconflow]:
        result = await provider(prompt, width, height)
        if result:
            return result
    return None

# ===================== AUTO GENERATION =====================
generating = False

async def auto_generate_catalog():
    global generating
    if generating:
        return
    generating = True
    catalog = load_catalog()
    existing_prompts = {img["prompt"] for img in catalog["images"]}

    print(f"[AutoGen] Starting image generation for store...")
    total_generated = 0

    for cat_key, cat_data in CATEGORIES.items():
        for prompt in cat_data["prompts_base"]:
            if prompt in existing_prompts:
                continue
            if total_generated >= 5:
                await asyncio.sleep(30)
                total_generated = 0

            print(f"[AutoGen] Generating: {cat_key} - {prompt[:50]}...")
            size = cat_data["sizes"][0]
            w, h = map(int, size.split("x"))
            w_gen = min(w, 1024)
            h_gen = min(h, 1024)

            img_data = await generate_image(prompt, w_gen, h_gen)
            if img_data:
                img_id = str(uuid.uuid4())[:8]
                filename = f"{cat_key}_{img_id}.png"
                filepath = IMAGES_DIR / filename

                with open(filepath, "wb") as f:
                    f.write(img_data)

                # Generate AI title and tags using Ollama
                title, tags = await generate_metadata(prompt, cat_key)

                image_entry = {
                    "id": img_id,
                    "category": cat_key,
                    "title": title,
                    "prompt": prompt,
                    "tags": tags,
                    "filename": filename,
                    "sizes": cat_data["sizes"],
                    "price": cat_data["price"],
                    "created_at": datetime.now().isoformat(),
                    "downloads": 0,
                    "views": 0
                }
                catalog["images"].append(image_entry)
                catalog["stats"]["total"] = len(catalog["images"])
                save_catalog(catalog)
                total_generated += 1
                print(f"[AutoGen] Created: {filename} - {title}")
            else:
                print(f"[AutoGen] Failed to generate: {prompt[:50]}")

            await asyncio.sleep(10)

    generating = False
    print(f"[AutoGen] Done! Total images in catalog: {len(catalog['images'])}")

async def generate_metadata(prompt: str, category: str):
    """Use Ollama to generate title and tags"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post("http://localhost:11434/api/generate", json={
                "model": "llama3.2:3b",
                "prompt": f"Generate a short catchy product title (max 8 words) and 5 SEO tags for this image: '{prompt}'. Category: {category}. Reply in format:\nTitle: <title>\nTags: tag1, tag2, tag3, tag4, tag5",
                "stream": False
            })
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                title = "AI Generated Image"
                tags = [category, "ai art", "digital"]
                for line in text.split("\n"):
                    if line.lower().startswith("title:"):
                        title = line.split(":", 1)[1].strip()[:80]
                    elif line.lower().startswith("tags:"):
                        tags = [t.strip() for t in line.split(":", 1)[1].split(",")][:8]
                return title, tags
    except:
        pass
    return f"AI {category.replace('_', ' ').title()} Art", [category, "ai", "digital art"]

# ===================== ROUTES =====================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    catalog = load_catalog()
    return templates.TemplateResponse("store.html", {
        "request": request,
        "categories": CATEGORIES,
        "catalog": catalog,
        "images": catalog.get("images", [])[-30:]
    })

@app.get("/category/{cat}", response_class=HTMLResponse)
async def category_page(request: Request, cat: str):
    catalog = load_catalog()
    images = [img for img in catalog["images"] if img["category"] == cat]
    cat_info = CATEGORIES.get(cat, {})
    return templates.TemplateResponse("category.html", {
        "request": request,
        "category": cat,
        "cat_info": cat_info,
        "images": images,
        "categories": CATEGORIES
    })

@app.get("/image/{img_id}", response_class=HTMLResponse)
async def image_detail(request: Request, img_id: str):
    catalog = load_catalog()
    image = next((img for img in catalog["images"] if img["id"] == img_id), None)
    if not image:
        return HTMLResponse("<h1>Image not found</h1>", status_code=404)
    image["views"] = image.get("views", 0) + 1
    save_catalog(catalog)
    return templates.TemplateResponse("image_detail.html", {
        "request": request,
        "image": image,
        "categories": CATEGORIES
    })

@app.get("/api/catalog")
async def api_catalog(category: str = None):
    catalog = load_catalog()
    images = catalog["images"]
    if category:
        images = [img for img in images if img["category"] == category]
    return {"images": images, "total": len(images), "stats": catalog["stats"]}

@app.post("/api/generate")
async def api_trigger_generation(background_tasks: BackgroundTasks):
    background_tasks.add_task(auto_generate_catalog)
    return {"status": "generating", "message": "Image generation started in background"}

@app.get("/api/search")
async def api_search(q: str = ""):
    catalog = load_catalog()
    if not q:
        return {"images": catalog["images"][:20]}
    q_lower = q.lower()
    results = [img for img in catalog["images"]
               if q_lower in img.get("title", "").lower()
               or q_lower in " ".join(img.get("tags", [])).lower()
               or q_lower in img.get("prompt", "").lower()]
    return {"images": results, "total": len(results)}

@app.get("/download/{img_id}")
async def download_image(img_id: str):
    catalog = load_catalog()
    image = next((img for img in catalog["images"] if img["id"] == img_id), None)
    if not image:
        return JSONResponse({"error": "not found"}, status_code=404)
    filepath = IMAGES_DIR / image["filename"]
    if not filepath.exists():
        return JSONResponse({"error": "file missing"}, status_code=404)
    image["downloads"] = image.get("downloads", 0) + 1
    catalog["stats"]["total_sales"] = catalog["stats"].get("total_sales", 0) + 1
    catalog["stats"]["revenue"] = catalog["stats"].get("revenue", 0) + image["price"]
    save_catalog(catalog)
    return FileResponse(str(filepath), filename=image["filename"], media_type="image/png")

# SEO sitemap
@app.get("/sitemap.xml")
async def sitemap():
    catalog = load_catalog()
    urls = ['<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    urls.append(f"<url><loc>https://ai-image-store.com/</loc><priority>1.0</priority></url>")
    for cat in CATEGORIES:
        urls.append(f"<url><loc>https://ai-image-store.com/category/{cat}</loc><priority>0.8</priority></url>")
    for img in catalog["images"]:
        urls.append(f"<url><loc>https://ai-image-store.com/image/{img['id']}</loc><priority>0.6</priority></url>")
    urls.append("</urlset>")
    return HTMLResponse("\n".join(urls), media_type="application/xml")

@app.on_event("startup")
async def startup():
    asyncio.create_task(auto_generate_catalog())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8017)
