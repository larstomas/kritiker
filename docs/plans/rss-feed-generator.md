# Kritiker.se RSS Feed Generator

## Context

Kritiker.se is a Swedish review aggregation site (films, series, albums, games) with no RSS feeds. The site has internal JSON APIs for listing items and detail pages with rich review data. Goal: build a tool that scrapes kritiker.se and generates standard RSS feeds.

## Discovery Summary

### Internal APIs found
| Category | API endpoint | Response fields |
|----------|-------------|-----------------|
| Films | `/api/film/cacha?typ=senaste` | `film`, `url`, `extradata` (director), `omslag`, `bakgrund`, `master` |
| Series | `/api/serie/cacha?typ=senaste` | `film`, `url`, `omslag`, `bakgrund`, `master`, `extra` |
| Albums | `/api/skiva/cacha?typ=senaste` | `artist`, `titel`, `url`, `omslag`, `bakgrund`, `master` |
| Games | `/api/spel/cacha?typ=senaste` | `titel`, `url`, `omslag`, `master` (currently returns 500) |

Other `typ` values: `basta`, `arsbasta`, `alla`, `sparade`, plus platform-specific for games (`switch`, `ps`, `xbox`, `pc`).

### Detail pages contain
- Kritiker score, IMDb score, Metacritic score
- Genre, director/artist, cast, release date, duration
- Individual critic reviews (publication + score)
- Streaming availability
- Plot summary

### Constraints
- ModSecurity WAF blocks some automated requests (need proper User-Agent)
- `/api/` is disallowed in robots.txt (but the site's own frontend uses it)
- Detail page scraping requires HTML parsing (BeautifulSoup)

## Solution: Python RSS Feed Generator

A Python script that fetches data from kritiker.se and generates RSS 2.0 XML feeds.

### Architecture

```
kritiker_se/
  kritiker_rss/
    __init__.py
    scraper.py      # API + HTML scraping logic
    feed.py         # RSS feed generation
    config.py       # Configuration (categories, URLs, cache settings)
  main.py           # CLI entry point
  requirements.txt
  docs/plans/       # This plan
```

### Implementation Steps

#### 1. Project setup
- Create `requirements.txt` with: `requests`, `beautifulsoup4`, `feedgen`, `lxml`
- Create `config.py` with base URL, API endpoints, category definitions, request headers

#### 2. Scraper module (`scraper.py`)
- `fetch_latest(category)` - calls the JSON API to get list of latest items
- `fetch_detail(url)` - scrapes an individual detail page for ratings, reviews, metadata
- Proper request headers (browser-like User-Agent) to avoid WAF blocks
- Rate limiting (1-2 second delay between detail page requests)
- Simple file-based cache for detail pages (avoid re-scraping unchanged items)

#### 3. Feed generator (`feed.py`)
- `generate_feed(category, items)` - creates RSS 2.0 XML using `feedgen`
- Each item includes: title, link, description (with ratings + reviews summary), pub date, image enclosure
- One feed per category: `filmer.xml`, `serier.xml`, `skivor.xml`, `spel.xml`

#### 4. CLI entry point (`main.py`)
- `python main.py` - generates all feeds to `output/` directory
- `python main.py --category filmer` - generate single category
- `python main.py --serve` - optional: start simple HTTP server to serve feeds
- `python main.py --opml` - generate OPML file for easy import into feed readers

### Feed content per item

Each RSS item will contain:
- **Title**: Film/album/series/game name (+ artist for albums, director for films)
- **Link**: Full URL to kritiker.se detail page
- **Description**: HTML-formatted summary with:
  - Kritiker score (e.g. "3.8/5")
  - IMDb / Metacritic scores if available
  - Genre, release date
  - Brief list of critic reviews (publication: score)
  - Streaming availability
- **Image**: Cover image as enclosure
- **GUID**: Based on the `master` ID from the API

### Rate limiting & caching strategy
- 1.5s delay between detail page requests
- Cache detail page results in `cache/` dir as JSON files keyed by `master` ID
- Cache TTL: 24 hours (reviews may be added over time)
- API list endpoints are always fetched fresh (they're lightweight)

## Verification

1. Run `python main.py` and check that XML files are generated in `output/`
2. Validate RSS XML with a feed validator
3. Import a feed into a reader (e.g. NetNewsWire, Feedly) and verify items display correctly
4. Run with `--serve` and subscribe to `http://localhost:8080/filmer.xml` in a feed reader

## Optional enhancements (not in initial scope)
- Docker container with cron for scheduled updates
- GitHub Actions workflow for hosting feeds on GitHub Pages
- Additional feed types: "best new", "year's best"
