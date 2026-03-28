#!/usr/bin/env python3
import argparse
import sys

from kritiker_rss import config
from kritiker_rss.scraper import fetch_latest, fetch_detail
from kritiker_rss.feed import generate_feed, generate_opml


def build_feeds(categories, skip_details=False):
    for category in categories:
        print(f"Processing {category}...")
        items = fetch_latest(category)
        if not items:
            print(f"  No items found for {category}, skipping")
            continue

        print(f"  Found {len(items)} items")

        if not skip_details:
            for i, item in enumerate(items):
                print(f"  Fetching detail {i + 1}/{len(items)}: {item['title']}")
                item["detail"] = fetch_detail(item["url"])
        else:
            for item in items:
                item["detail"] = {}

        output_path = generate_feed(category, items)
        print(f"  Generated {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate RSS feeds from Kritiker.se")
    parser.add_argument(
        "--category", "-c",
        choices=list(config.CATEGORIES.keys()),
        help="Generate feed for a single category only",
    )
    parser.add_argument(
        "--skip-details",
        action="store_true",
        help="Skip fetching detail pages (faster, less data)",
    )
    parser.add_argument(
        "--opml",
        action="store_true",
        help="Generate OPML file for feed reader import",
    )
    parser.add_argument(
        "--pages-url",
        help="Base URL for GitHub Pages (used in OPML)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        help="Output directory for generated feeds",
    )
    args = parser.parse_args()

    if args.output_dir:
        config.OUTPUT_DIR = args.output_dir

    categories = [args.category] if args.category else list(config.CATEGORIES.keys())

    build_feeds(categories, skip_details=args.skip_details)

    if args.opml:
        opml_path = generate_opml(categories, pages_url=args.pages_url)
        print(f"Generated {opml_path}")

    print("Done!")


if __name__ == "__main__":
    main()
