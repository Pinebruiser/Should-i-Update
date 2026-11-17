import json
import os
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_cache_path() -> Path:
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        base = Path(xdg_cache) / "should-i-update"
    else:
        base = Path.home() / ".cache" / "should-i-update"
    base.mkdir(parents=True, exist_ok=True)
    return base / "arch_news.json"


def fetch_arch_news(max_items: int = 5, timeout: float = 3.5) -> List[Dict[str, str]]:
    """Fetch recent Arch Linux news items with local caching (1 hour TTL)."""
    cache_file = get_cache_path()
    now = time.time()

    # Check cache
    if cache_file.is_file():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if now - data.get("timestamp", 0) < 3600:
                    return data.get("items", [])[:max_items]
        except Exception:
            pass

    # Fetch from RSS
    url = "https://archlinux.org/feeds/news/"
    items: List[Dict[str, str]] = []
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Should-i-Update/1.0 (Arch Linux Package Assistant)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            root = ET.fromstring(content)
            for entry in root.findall("./channel/item")[:max_items]:
                title = entry.findtext("title", "").strip()
                desc = entry.findtext("description", "").strip()
                link = entry.findtext("link", "").strip()
                pub_date = entry.findtext("pubDate", "").strip()
                # Clean html tags from description if any
                clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()
                clean_desc = " ".join(clean_desc.split())[:300]
                if title:
                    items.append({
                        "title": title,
                        "description": clean_desc,
                        "link": link,
                        "pub_date": pub_date,
                    })

        # Save to cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": now, "items": items}, f)

    except Exception:
        # If fetch fails, try to return stale cache if available
        if cache_file.is_file():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f).get("items", [])[:max_items]
            except Exception:
                pass
        return []

    return items[:max_items]


def find_news_matches(package_names: List[str], news_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Find news items that mention any of the pending packages."""
    matches = []
    pkg_set = set(p.lower() for p in package_names)

    for item in news_items:
        text = f"{item['title']} {item['description']}".lower()
        for pkg in pkg_set:
            if re.search(r"\b" + re.escape(pkg) + r"\b", text):
                matches.append(item)
                break

    return matches

