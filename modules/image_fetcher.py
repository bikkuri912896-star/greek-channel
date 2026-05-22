import requests
import random
import hashlib
from pathlib import Path
import config


def _cache_path(url: str) -> Path:
    h = hashlib.md5(url.encode()).hexdigest()
    return config.IMAGE_CACHE_DIR / f"{h}.jpg"


def _download(url: str) -> Path | None:
    cache = _cache_path(url)
    if cache.exists():
        return cache
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        cache.write_bytes(r.content)
        return cache
    except Exception as e:
        print(f"[image_fetcher] Download failed: {url} — {e}")
        return None


def _search_met(query: str, max_results: int = 20) -> list[str]:
    try:
        search_url = f"{config.MET_API_BASE}/search"
        params = {
            "q": query,
            "departmentId": config.MET_DEPARTMENT_GREEK_ROMAN,
            "isPublicDomain": "true",
            "hasImages": "true",
        }
        r = requests.get(search_url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        object_ids = data.get("objectIDs") or []
        random.shuffle(object_ids)
        image_urls = []
        for oid in object_ids[:max_results * 3]:
            if len(image_urls) >= max_results:
                break
            try:
                obj_r = requests.get(f"{config.MET_API_BASE}/objects/{oid}", timeout=8)
                obj_data = obj_r.json()
                if obj_data.get("isPublicDomain") and obj_data.get("primaryImage"):
                    image_urls.append(obj_data["primaryImage"])
            except Exception:
                continue
        return image_urls
    except Exception as e:
        print(f"[image_fetcher] Met search failed: {query} — {e}")
        return []


def fetch_images(topic: dict, count: int = 4) -> list[Path]:
    queries = [
        topic.get("theme", "ancient greek"),
        "ancient greek sculpture",
        "greek vase painting",
        "ancient greece philosophy",
    ]

    all_urls = []
    for q in queries:
        urls = _search_met(q)
        all_urls.extend(urls)
        if len(all_urls) >= count * 3:
            break

    random.shuffle(all_urls)
    paths = []
    for url in all_urls:
        if len(paths) >= count:
            break
        p = _download(url)
        if p:
            paths.append(p)

    return paths
