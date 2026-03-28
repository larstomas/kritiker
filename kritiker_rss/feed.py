from datetime import datetime, timezone
from pathlib import Path

from feedgen.feed import FeedGenerator

from . import config


def generate_feed(category, items, base_url=None):
    if base_url is None:
        base_url = config.BASE_URL

    cat_config = config.CATEGORIES[category]
    fg = FeedGenerator()
    fg.title(cat_config["feed_title"])
    fg.link(href=f"{config.BASE_URL}/{category}/", rel="alternate")
    fg.description(cat_config["feed_description"])
    fg.language("sv")
    fg.lastBuildDate(datetime.now(timezone.utc))

    for item in items:
        fe = fg.add_entry()

        title = item["title"]
        if item.get("artist"):
            title = f"{item['artist']} - {title}"
        elif item.get("director"):
            title = f"{title} ({item['director']})"
        detail = item.get("detail", {})
        if detail.get("rating"):
            title = f"[{detail['rating']}] {title}"
        fe.title(title)

        full_url = config.BASE_URL + item["url"]
        fe.link(href=full_url)
        rating = detail.get("rating", "")
        fe.guid(f"{full_url}#rating-{rating}" if rating else full_url, permalink=False)

        description = _build_description(item, detail)
        fe.description(description)

        if item.get("image"):
            fe.enclosure(item["image"], 0, "image/jpeg")

        if detail.get("release_date"):
            fe.published(datetime.now(timezone.utc))

    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{category}.xml"
    fg.rss_file(str(output_path), pretty=True)
    return output_path


def _build_description(item, detail):
    parts = []

    if detail.get("description"):
        parts.append(f"<p>{detail['description']}</p>")

    meta = []
    if detail.get("rating"):
        meta.append(f"<strong>Betyg:</strong> {detail['rating']}")
    if detail.get("genre"):
        meta.append(f"<strong>Genre:</strong> {detail['genre']}")
    if detail.get("release_date"):
        meta.append(f"<strong>Premiär:</strong> {detail['release_date']}")
    if item.get("artist"):
        meta.append(f"<strong>Artist:</strong> {item['artist']}")
    if item.get("director"):
        meta.append(f"<strong>Regissör:</strong> {item['director']}")
    if meta:
        parts.append("<p>" + " | ".join(meta) + "</p>")

    if detail.get("streaming"):
        parts.append(f"<p><strong>Streama:</strong> {', '.join(detail['streaming'])}</p>")

    if detail.get("reviews"):
        rows = "".join(
            f"<tr><td>{r['publication']}</td><td>{r['score']}</td></tr>"
            for r in detail["reviews"]
        )
        parts.append(
            f"<table><tr><th>Källa</th><th>Betyg</th></tr>{rows}</table>"
        )

    if item.get("image"):
        parts.insert(0, f'<img src="{item["image"]}" width="200" />')

    return "\n".join(parts) if parts else item["title"]


def generate_opml(categories, pages_url=None):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<opml version="2.0">',
        "<head><title>Kritiker.se RSS Feeds</title></head>",
        "<body>",
    ]
    for cat in categories:
        cat_config = config.CATEGORIES[cat]
        if pages_url:
            xml_url = f"{pages_url}/{cat}.xml"
        else:
            xml_url = f"{cat}.xml"
        lines.append(
            f'  <outline text="{cat_config["feed_title"]}" '
            f'type="rss" xmlUrl="{xml_url}" />'
        )
    lines.append("</body>")
    lines.append("</opml>")

    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "kritiker.opml"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
