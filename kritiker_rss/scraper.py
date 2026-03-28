import html
import json
import os
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from . import config


session = requests.Session()
session.headers.update(config.HEADERS)


def fetch_latest(category):
    cat_config = config.CATEGORIES[category]
    url = config.BASE_URL + cat_config["api"]
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"  Warning: API request failed for {category}: {e}")
        return []

    if isinstance(data, dict):
        data = [data]

    items = []
    for raw in data:
        title = html.unescape(raw.get(cat_config["title_field"], ""))
        if not title:
            continue
        item = {
            "title": title,
            "url": raw.get("url", ""),
            "image": raw.get("omslag", ""),
            "master": raw.get("master"),
        }
        if "artist" in raw:
            item["artist"] = html.unescape(raw["artist"])
        if "extradata" in raw and raw["extradata"]:
            item["director"] = html.unescape(raw["extradata"])
        items.append(item)

    return items


def fetch_detail(item_url):
    cache_path = _cache_path(item_url)
    cached = _read_cache(cache_path)
    if cached is not None:
        return cached

    full_url = config.BASE_URL + item_url
    try:
        resp = session.get(full_url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Warning: detail page failed for {item_url}: {e}")
        return {}

    detail = _parse_detail_page(resp.text)
    _write_cache(cache_path, detail)
    time.sleep(config.REQUEST_DELAY)
    return detail


def _parse_detail_page(html):
    soup = BeautifulSoup(html, "lxml")
    detail = {}

    # Average grade from #betyg > p.grade (score encoded in class e.g. grade39 = 3.9)
    import re
    grade_el = soup.select_one("#betyg > p.grade")
    if grade_el:
        for cls in grade_el.get("class", []):
            m = re.match(r"grade(\d+)", cls)
            if m and cls != "grade":
                raw = m.group(1)
                detail["rating"] = f"{raw[0]}.{raw[1:]}" if len(raw) > 1 else raw
                break
        if "rating" not in detail:
            text = grade_el.get_text(strip=True)
            if text:
                detail["rating"] = text

    # Genre - try #data > p:nth-child(2) first, then fallback to text search
    genre_el = soup.select_one("#data > p:nth-child(2)")
    if genre_el:
        genre = genre_el.get_text(strip=True)
        if genre:
            detail["genre"] = genre
    else:
        for label in soup.find_all(string=lambda t: t and "Genre" in t):
            parent = label.parent
            if parent:
                sibling_text = parent.get_text(strip=True)
                genre = sibling_text.replace("Genre:", "").replace("Genre", "").strip()
                if genre:
                    detail["genre"] = genre
                    break

    # Release date - look for a date pattern near "Premiär"
    for label in soup.find_all(string=lambda t: t and "Premiär" in t):
        parent = label.parent
        if parent:
            # Check next sibling or parent's next element for date text
            next_el = parent.find_next_sibling()
            if next_el:
                date_text = next_el.get_text(strip=True)
            else:
                date_text = parent.get_text(strip=True)
                date_text = date_text.replace("Premiär:", "").replace("Premiär", "").strip()
            # Only accept if it looks like a date (contains digits)
            if date_text and any(c.isdigit() for c in date_text):
                detail["release_date"] = date_text
                break

    # Description / synopsis
    for meta in soup.find_all("meta", attrs={"name": "description"}):
        content = meta.get("content", "").strip()
        if content:
            detail["description"] = content
            break

    # Critic reviews
    reviews = []
    # Look for review-like table rows or list items
    for row in soup.select("tr, .review, .recension, [class*=recens]"):
        cells = row.find_all(["td", "span", "div"])
        if len(cells) >= 2:
            pub = cells[0].get_text(strip=True)
            score = cells[-1].get_text(strip=True)
            if pub and score and len(pub) < 50 and len(score) < 15:
                reviews.append({"publication": pub, "score": score})
    if reviews:
        detail["reviews"] = reviews[:15]

    # Streaming availability - look for links within the main content area only,
    # excluding the site-wide nav/footer which links to streaming filter pages
    known_services = {"Netflix", "Max", "HBO Max", "Viaplay", "Disney+", "Prime Video",
                      "Apple TV+", "Spotify", "SVT Play", "TV4 Play", "Cineasterna"}
    streaming = []
    # Only match links that point to external streaming sites (not internal /filmer/ pages)
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        name = link.get_text(strip=True)
        if name in known_services and name not in streaming and not href.startswith("/"):
            streaming.append(name)
    if streaming:
        detail["streaming"] = streaming

    return detail


def _cache_path(item_url):
    safe_name = item_url.strip("/").replace("/", "_") + ".json"
    return Path(config.CACHE_DIR) / safe_name


def _read_cache(path):
    if not path.exists():
        return None
    try:
        age_hours = (time.time() - path.stat().st_mtime) / 3600
        if age_hours > 24:
            return None
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
