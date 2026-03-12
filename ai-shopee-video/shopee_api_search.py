#!/usr/bin/env python3
"""
Busca produtos no Shopee via API interna (evita captcha do navegador)
"""
import httpx, json, sys, os, hashlib
from datetime import datetime

try:
    sys.stdout.reconfigure(line_buffering=True)
except:
    pass
DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://shopee.com.br/",
    "X-Shopee-Language": "pt-BR",
    "X-Requested-With": "XMLHttpRequest",
}

def buscar_shopee(keyword, limit=10):
    """Busca produtos via API de busca do Shopee"""
    url = "https://shopee.com.br/api/v4/search/search_items"
    params = {
        "by": "relevancy",
        "keyword": keyword,
        "limit": limit,
        "newest": 0,
        "order": "desc",
        "page_type": "search",
        "scenario": "PAGE_GLOBAL_SEARCH",
        "version": 2,
    }
    
    try:
        with httpx.Client(timeout=15, headers=HEADERS) as client:
            resp = client.get(url, params=params)
            data = resp.json()
            
            items = data.get("items", [])
            produtos = []
            for item in items:
                info = item.get("item_basic", {})
                shop_id = info.get("shopid", "")
                item_id = info.get("itemid", "")
                name = info.get("name", "")
                price = info.get("price", 0) / 100000  # Shopee uses cents * 1000
                sold = info.get("historical_sold", 0)
                rating = info.get("item_rating", {}).get("rating_star", 0)
                image = info.get("image", "")
                
                product_url = f"https://shopee.com.br/product-i.{shop_id}.{item_id}"
                
                produtos.append({
                    "titulo": name[:80],
                    "url": product_url,
                    "preco": f"R$ {price:.2f}",
                    "vendidos": sold,
                    "avaliacao": round(rating, 1),
                    "imagem": f"https://cf.shopee.com.br/file/{image}" if image else "",
                    "shop_id": shop_id,
                    "item_id": item_id,
                })
            
            return produtos
    except Exception as e:
        print(f"[API] Erro: {e}")
        return []

def get_product_detail(shop_id, item_id):
    """Busca detalhes do produto (todas as imagens, descrição completa)"""
    url = "https://shopee.com.br/api/v4/item/get"
    params = {"shopid": shop_id, "itemid": item_id}
    try:
        with httpx.Client(timeout=15, headers=HEADERS) as client:
            resp = client.get(url, params=params)
            data = resp.json()
            item = data.get("data", {})
            images = item.get("images", [])
            image_urls = [f"https://cf.shopee.com.br/file/{img}" for img in images if img]
            return {
                "images": image_urls,
                "description": item.get("description", ""),
                "name": item.get("name", ""),
                "price": item.get("price", 0) / 100000,
                "stock": item.get("stock", 0),
                "sold": item.get("historical_sold", 0),
                "rating": item.get("item_rating", {}).get("rating_star", 0),
                "rating_count": item.get("item_rating", {}).get("rating_count", [0]*6),
            }
    except Exception as e:
        print(f"[API] Erro detail: {e}")
        return {"images": [], "description": "", "name": "", "price": 0, "sold": 0, "rating": 0}

def buscar_populares(keyword, limit=5):
    """Busca e retorna os mais populares (por vendidos)"""
    prods = buscar_shopee(keyword, limit=limit * 2)
    prods.sort(key=lambda x: x.get("vendidos", 0), reverse=True)
    return prods[:limit]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", help="Termo de busca")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    
    prods = buscar_populares(args.keyword, args.limit)
    print(f"\n🔍 Busca: '{args.keyword}' - {len(prods)} resultados\n")
    for p in prods:
        print(f"  🛒 {p['titulo'][:50]}")
        print(f"     {p['preco']} | ⭐{p['avaliacao']} | 🛍️{p['vendidos']} vendidos")
        print(f"     {p['url']}")
        print()
    
    # Salvar resultados
    with open("search_results.json", "w") as f:
        json.dump(prods, f, indent=2, ensure_ascii=False)
    print(f"💾 Resultados salvos em search_results.json")
