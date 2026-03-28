BASE_URL = "https://www.kritiker.se"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}

REQUEST_DELAY = 1.5  # seconds between detail page requests

CATEGORIES = {
    "filmer": {
        "api": "/api/film/cacha?typ=senaste",
        "title_field": "film",
        "feed_title": "Kritiker.se - Senaste filmer",
        "feed_description": "Senaste filmrecensioner från Kritiker.se",
    },
    "serier": {
        "api": "/api/serie/cacha?typ=senaste",
        "title_field": "film",
        "feed_title": "Kritiker.se - Senaste serier",
        "feed_description": "Senaste serierecensioner från Kritiker.se",
    },
    "skivor": {
        "api": "/api/skiva/cacha?typ=senaste",
        "title_field": "titel",
        "feed_title": "Kritiker.se - Senaste skivor",
        "feed_description": "Senaste skivrecensioner från Kritiker.se",
    },
    "spel": {
        "api": "/api/spel/cacha?typ=basta",
        "title_field": "titel",
        "feed_title": "Kritiker.se - Bästa nya spel",
        "feed_description": "Bästa nya spelrecensioner från Kritiker.se",
    },
}

CACHE_DIR = "cache"
OUTPUT_DIR = "output"
