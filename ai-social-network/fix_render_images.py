"""
Replace local image paths with external Pixabay/Pexels URLs
so images work on Render deployment
"""
import sqlite3
import random
import urllib.request
import urllib.parse
import json
import time
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "instagram.db")

# Pixabay API (free, 500 req/hour)
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "")

# Curated high-quality image URLs from Pixabay CDN (permanent, no expiry)
# These are direct CDN links that never expire
FALLBACK_IMAGES = {
    "technology": [
        "https://cdn.pixabay.com/photo/2016/11/19/14/00/code-1839406_640.jpg",
        "https://cdn.pixabay.com/photo/2017/05/10/19/29/robot-2301646_640.jpg",
        "https://cdn.pixabay.com/photo/2018/09/27/09/22/artificial-intelligence-3706562_640.jpg",
        "https://cdn.pixabay.com/photo/2019/02/06/16/32/vintage-3979258_640.jpg",
        "https://cdn.pixabay.com/photo/2017/12/10/17/40/background-3010856_640.jpg",
        "https://cdn.pixabay.com/photo/2020/01/16/18/10/macos-4770450_640.jpg",
        "https://cdn.pixabay.com/photo/2016/12/28/09/36/web-1935737_640.png",
        "https://cdn.pixabay.com/photo/2021/08/04/13/06/software-developer-6521720_640.jpg",
        "https://cdn.pixabay.com/photo/2015/01/08/18/27/startup-593341_640.jpg",
        "https://cdn.pixabay.com/photo/2016/11/30/20/58/programming-1873854_640.png",
    ],
    "robot": [
        "https://cdn.pixabay.com/photo/2018/03/31/06/31/dog-3277416_640.jpg",
        "https://cdn.pixabay.com/photo/2019/03/29/10/56/artificial-intelligence-4089128_640.jpg",
        "https://cdn.pixabay.com/photo/2017/01/08/21/37/flame-1964066_640.jpg",
        "https://cdn.pixabay.com/photo/2020/10/21/18/07/light-bulb-5673794_640.jpg",
        "https://cdn.pixabay.com/photo/2018/05/08/08/44/artificial-intelligence-3382507_640.jpg",
        "https://cdn.pixabay.com/photo/2019/07/14/16/27/pen-4337521_640.jpg",
        "https://cdn.pixabay.com/photo/2023/02/04/17/28/chat-7767693_640.jpg",
        "https://cdn.pixabay.com/photo/2024/02/07/13/45/ai-generated-8559323_640.jpg",
    ],
    "nature": [
        "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_640.jpg",
        "https://cdn.pixabay.com/photo/2013/10/02/23/03/mountains-190055_640.jpg",
        "https://cdn.pixabay.com/photo/2016/05/05/02/37/sunset-1373171_640.jpg",
        "https://cdn.pixabay.com/photo/2018/01/14/23/12/nature-3082832_640.jpg",
        "https://cdn.pixabay.com/photo/2014/02/27/16/10/flowers-276014_640.jpg",
        "https://cdn.pixabay.com/photo/2015/12/01/20/28/road-1072821_640.jpg",
        "https://cdn.pixabay.com/photo/2018/08/14/13/23/ocean-3605547_640.jpg",
        "https://cdn.pixabay.com/photo/2017/02/08/17/24/fantasy-2049567_640.jpg",
    ],
    "art": [
        "https://cdn.pixabay.com/photo/2017/08/30/01/05/milky-way-2695569_640.jpg",
        "https://cdn.pixabay.com/photo/2018/08/16/08/39/painting-3609894_640.jpg",
        "https://cdn.pixabay.com/photo/2017/01/18/16/46/hong-kong-1990268_640.jpg",
        "https://cdn.pixabay.com/photo/2020/04/05/10/17/galaxy-5005098_640.jpg",
        "https://cdn.pixabay.com/photo/2016/09/10/17/18/book-1659717_640.jpg",
        "https://cdn.pixabay.com/photo/2018/01/12/10/19/fantasy-3077928_640.jpg",
        "https://cdn.pixabay.com/photo/2019/10/08/19/54/forest-4535091_640.jpg",
        "https://cdn.pixabay.com/photo/2022/12/01/04/42/man-7628305_640.jpg",
    ],
    "city": [
        "https://cdn.pixabay.com/photo/2017/12/10/20/53/city-3010583_640.jpg",
        "https://cdn.pixabay.com/photo/2016/01/19/17/53/car-1149997_640.jpg",
        "https://cdn.pixabay.com/photo/2017/03/29/04/47/high-rise-2184108_640.jpg",
        "https://cdn.pixabay.com/photo/2019/07/21/02/11/building-4352630_640.jpg",
        "https://cdn.pixabay.com/photo/2014/08/01/00/08/new-york-city-407703_640.jpg",
        "https://cdn.pixabay.com/photo/2016/11/06/05/36/building-1802412_640.jpg",
        "https://cdn.pixabay.com/photo/2020/02/21/14/49/tokyo-4867420_640.jpg",
        "https://cdn.pixabay.com/photo/2015/05/15/14/27/eiffel-tower-768501_640.jpg",
    ],
    "space": [
        "https://cdn.pixabay.com/photo/2011/12/14/12/21/orion-nebula-11107_640.jpg",
        "https://cdn.pixabay.com/photo/2016/10/20/18/35/earth-1756274_640.jpg",
        "https://cdn.pixabay.com/photo/2016/02/01/00/56/universe-1172114_640.jpg",
        "https://cdn.pixabay.com/photo/2015/03/26/18/31/milky-way-693521_640.jpg",
        "https://cdn.pixabay.com/photo/2017/08/30/01/05/milky-way-2695569_640.jpg",
        "https://cdn.pixabay.com/photo/2020/06/01/22/27/galaxy-5248274_640.jpg",
        "https://cdn.pixabay.com/photo/2016/10/10/12/48/astronaut-1728672_640.jpg",
        "https://cdn.pixabay.com/photo/2013/07/18/20/26/space-164922_640.jpg",
    ],
    "abstract": [
        "https://cdn.pixabay.com/photo/2018/01/11/21/27/smoke-3076685_640.jpg",
        "https://cdn.pixabay.com/photo/2017/01/08/19/52/nebula-1963093_640.jpg",
        "https://cdn.pixabay.com/photo/2016/06/02/02/33/triangles-1430105_640.png",
        "https://cdn.pixabay.com/photo/2019/07/30/18/26/surface-4373588_640.jpg",
        "https://cdn.pixabay.com/photo/2018/09/04/10/27/never-stop-learning-3653430_640.jpg",
        "https://cdn.pixabay.com/photo/2016/07/27/08/56/diamonds-1544726_640.jpg",
        "https://cdn.pixabay.com/photo/2020/06/19/22/33/wormhole-5319067_640.jpg",
        "https://cdn.pixabay.com/photo/2018/03/22/02/37/background-3249063_640.png",
    ],
    "food": [
        "https://cdn.pixabay.com/photo/2017/05/23/22/36/vegetables-2338824_640.jpg",
        "https://cdn.pixabay.com/photo/2016/11/29/12/54/cafe-1869656_640.jpg",
        "https://cdn.pixabay.com/photo/2017/01/11/11/33/cake-1971552_640.jpg",
        "https://cdn.pixabay.com/photo/2015/02/14/04/30/coffee-636180_640.jpg",
        "https://cdn.pixabay.com/photo/2017/12/09/08/18/pizza-3007395_640.jpg",
        "https://cdn.pixabay.com/photo/2016/03/05/19/02/hamburger-1238246_640.jpg",
    ],
    "music": [
        "https://cdn.pixabay.com/photo/2015/05/07/11/02/guitar-756326_640.jpg",
        "https://cdn.pixabay.com/photo/2016/11/19/10/46/concert-1838412_640.jpg",
        "https://cdn.pixabay.com/photo/2017/11/07/00/07/fantasy-2925250_640.jpg",
        "https://cdn.pixabay.com/photo/2016/08/01/20/15/girl-1561979_640.jpg",
        "https://cdn.pixabay.com/photo/2018/09/17/14/27/headphones-3683983_640.jpg",
        "https://cdn.pixabay.com/photo/2016/11/22/19/15/hand-1850120_640.jpg",
    ],
}

# Keywords to match categories
CATEGORY_KEYWORDS = {
    "technology": ["tech", "code", "programming", "software", "digital", "computer", "algorithm", "data", "neural", "network", "machine", "learning", "cpu", "binary", "innovation", "startup", "hack"],
    "robot": ["robot", "ai", "artificial", "intelligence", "bot", "android", "cyborg", "automation", "chatbot", "llm", "model", "gpt", "llama", "gemma", "phi", "qwen", "mistral", "tinyllama", "deepseek", "claude", "gemini", "grok", "nvidia"],
    "nature": ["nature", "tree", "flower", "forest", "ocean", "sea", "mountain", "river", "garden", "animal", "sunset", "sunrise", "landscape", "earth", "green", "wildlife"],
    "art": ["art", "painting", "creative", "canvas", "design", "aesthetic", "beauty", "surreal", "fantasy", "dream", "imagine", "poetry", "literature", "book", "music", "dance"],
    "city": ["city", "urban", "building", "street", "architecture", "night", "lights", "skyscraper", "downtown", "traffic", "bridge", "road", "car", "neon", "metro"],
    "space": ["space", "star", "galaxy", "universe", "cosmos", "planet", "moon", "sun", "nebula", "orbit", "astronaut", "nasa", "rocket", "alien", "milky"],
    "abstract": ["abstract", "pattern", "geometric", "color", "wave", "fractal", "infinity", "matrix", "dimension", "quantum", "energy", "vibration", "light"],
    "food": ["food", "coffee", "cafe", "cooking", "recipe", "kitchen", "delicious", "pizza", "cake", "breakfast", "lunch", "dinner", "restaurant", "chef"],
    "music": ["music", "song", "melody", "rhythm", "beat", "guitar", "piano", "concert", "band", "dj", "spotify", "album", "vinyl"],
}

def categorize_caption(caption):
    """Determine best image category based on caption text"""
    if not caption:
        return "technology"
    
    caption_lower = caption.lower()
    scores = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in caption_lower)
        if score > 0:
            scores[category] = score
    
    if scores:
        return max(scores, key=scores.get)
    
    # Default based on common AI themes
    return random.choice(["technology", "robot", "abstract", "space", "art"])

def main():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    
    # Get all posts with local images
    cursor = db.execute(
        "SELECT id, caption, imagem_url, agente_id FROM ig_posts WHERE imagem_url LIKE '/static/%'"
    )
    posts = cursor.fetchall()
    
    print(f"Found {len(posts)} posts with local images")
    
    # Track used URLs to avoid duplicates
    used_urls = set()
    updated = 0
    
    for post in posts:
        caption = post["caption"] or ""
        category = categorize_caption(caption)
        
        # Pick a random image from the category
        available = [url for url in FALLBACK_IMAGES[category] if url not in used_urls]
        if not available:
            # Reset if all used in this category
            available = FALLBACK_IMAGES[category]
        
        new_url = random.choice(available)
        used_urls.add(new_url)
        
        # Update the database
        db.execute(
            "UPDATE ig_posts SET imagem_url = ?, img_generator = ? WHERE id = ?",
            (new_url, f"Pixabay ({category})", post["id"])
        )
        updated += 1
    
    # Also fix carousel_urls that have local paths
    cursor2 = db.execute(
        "SELECT id, carousel_urls FROM ig_posts WHERE carousel_urls IS NOT NULL AND carousel_urls LIKE '%/static/%'"
    )
    carousel_posts = cursor2.fetchall()
    print(f"Found {len(carousel_posts)} posts with local carousel images")
    
    for cp in carousel_posts:
        import json
        urls = json.loads(cp["carousel_urls"])
        new_urls = []
        for url in urls:
            if url.startswith("/static/"):
                category = random.choice(list(FALLBACK_IMAGES.keys()))
                new_urls.append(random.choice(FALLBACK_IMAGES[category]))
            else:
                new_urls.append(url)
        db.execute(
            "UPDATE ig_posts SET carousel_urls = ? WHERE id = ?",
            (json.dumps(new_urls), cp["id"])
        )
    
    # Fix story images too
    cursor3 = db.execute(
        "SELECT id, texto FROM ig_stories WHERE imagem_url LIKE '/static/%'"
    )
    stories = cursor3.fetchall()
    print(f"Found {len(stories)} stories with local images")
    
    for s in stories:
        category = categorize_caption(s["texto"] or "")
        new_url = random.choice(FALLBACK_IMAGES[category])
        db.execute(
            "UPDATE ig_stories SET imagem_url = ? WHERE id = ?",
            (new_url, s["id"])
        )
    
    db.commit()
    db.close()
    
    print(f"\nDone! Updated {updated} posts, {len(carousel_posts)} carousels, {len(stories)} stories")
    print("All local image paths replaced with Pixabay CDN URLs (permanent, no expiry)")

if __name__ == "__main__":
    main()
