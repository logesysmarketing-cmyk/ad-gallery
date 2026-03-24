#!/usr/bin/env python3
"""
Meta Ad Library Scraper using Apify (automly/facebook-ad-library-scraper)
Scrapes ads, filters for 30+ day runners, downloads images, and builds an HTML gallery.

Usage:
    export APIFY_API_TOKEN="your_token_here"
    python3 scrape_meta_ads.py
"""

import os
import sys
import json
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN", "")
ACTOR_ID = "automly~facebook-ad-library-scraper"
TODAY = date(2026, 3, 24)

SEARCH_TERMS = [
    "data engineering",
    "data bricks services",
    "data analytics",
    "workflow automation",
]

COUNTRIES = ["IN", "US", "AE"]  # AE = UAE

MAX_ADS = 50
AD_TYPE = "IMAGE"
MIN_DAYS_RUNNING = 30

OUTPUT_DIR = Path("ad-gallery")
IMAGES_DIR = OUTPUT_DIR / "images"


def run_apify_actor(search_term: str, country: str) -> list:
    """Run the Apify actor for a single search term + country combo."""
    import urllib.request
    import urllib.parse

    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
    params = urllib.parse.urlencode({"token": APIFY_TOKEN})
    full_url = f"{url}?{params}"

    payload = json.dumps({
        "searchTerms": [search_term],
        "country": country,
        "adType": AD_TYPE,
        "maxAds": MAX_ADS,
    }).encode("utf-8")

    req = urllib.request.Request(
        full_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    print(f"  Scraping: '{search_term}' in {country}...")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"    -> Got {len(data)} results")
            return data
    except urllib.error.HTTPError as e:
        print(f"    -> HTTP Error {e.code}: {e.reason}")
        return []
    except Exception as e:
        print(f"    -> Error: {e}")
        return []


def deduplicate_ads(all_ads: list) -> list:
    """Remove duplicate ads based on ad ID."""
    seen = set()
    unique = []
    for ad in all_ads:
        ad_id = ad.get("adArchiveID") or ad.get("adid") or ad.get("id") or json.dumps(ad, sort_keys=True)
        if isinstance(ad_id, dict):
            ad_id = json.dumps(ad_id, sort_keys=True)
        ad_id_str = str(ad_id)
        if ad_id_str not in seen:
            seen.add(ad_id_str)
            unique.append(ad)
    return unique


def parse_date(date_str: str) -> date | None:
    """Parse various date formats."""
    if not date_str:
        return None
    for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%b %d, %Y", "%d/%m/%Y"]:
        try:
            return datetime.strptime(date_str.split("T")[0] if "T" in date_str else date_str, fmt.split("T")[0]).date()
        except ValueError:
            continue
    return None


def get_ad_start_date(ad: dict) -> date | None:
    """Extract start date from ad data."""
    for key in ["startDate", "start_date", "adStartDate", "startedRunningOn", "ad_delivery_start_time", "created_time"]:
        val = ad.get(key)
        if val:
            d = parse_date(str(val))
            if d:
                return d
    snapshot = ad.get("snapshot", {})
    if isinstance(snapshot, dict):
        for key in ["creation_time", "start_date"]:
            val = snapshot.get(key)
            if val:
                d = parse_date(str(val))
                if d:
                    return d
    return None


def get_image_url(ad: dict) -> str | None:
    """Extract image URL from ad data."""
    for key in ["imageUrl", "image_url", "adImageUrl", "thumbnailUrl", "image", "mediaUrl"]:
        val = ad.get(key)
        if val and isinstance(val, str) and val.startswith("http"):
            return val

    snapshot = ad.get("snapshot", {})
    if isinstance(snapshot, dict):
        images = snapshot.get("images", [])
        if images and isinstance(images, list):
            img = images[0]
            if isinstance(img, dict):
                return img.get("original_image_url") or img.get("resized_image_url") or img.get("url")
            elif isinstance(img, str):
                return img
        for key in ["image_url", "imageUrl", "thumbnail_url"]:
            val = snapshot.get(key)
            if val:
                return val

    cards = ad.get("cards", []) or ad.get("snapshot", {}).get("cards", [])
    if cards and isinstance(cards, list):
        card = cards[0]
        if isinstance(card, dict):
            return card.get("original_image_url") or card.get("resized_image_url")

    return None


def get_ad_text(ad: dict) -> str:
    """Extract ad copy/text."""
    for key in ["adText", "ad_text", "body", "description", "adBody", "ad_creative_body", "text"]:
        val = ad.get(key)
        if val and isinstance(val, str):
            return val

    snapshot = ad.get("snapshot", {})
    if isinstance(snapshot, dict):
        body = snapshot.get("body", {})
        if isinstance(body, dict):
            return body.get("text", "") or body.get("markup", {}).get("__html", "")
        elif isinstance(body, str):
            return body
        for key in ["title", "caption", "link_description"]:
            val = snapshot.get(key)
            if val:
                return str(val)

    return "No ad text available"


def get_brand_name(ad: dict) -> str:
    """Extract brand/page name."""
    for key in ["pageName", "page_name", "brandName", "advertiser", "advertiserName", "pageAlias"]:
        val = ad.get(key)
        if val and isinstance(val, str):
            return val
    snapshot = ad.get("snapshot", {})
    if isinstance(snapshot, dict):
        return snapshot.get("page_name", "") or snapshot.get("title", "")
    return "Unknown Brand"


def download_image(url: str, filename: str) -> bool:
    """Download an image from URL."""
    filepath = IMAGES_DIR / filename
    if filepath.exists():
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            filepath.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"    Failed to download {url}: {e}")
        return False


def process_ads(all_ads: list) -> list:
    """Process, filter, and prepare ads for the gallery."""
    unique_ads = deduplicate_ads(all_ads)
    print(f"\nAfter deduplication: {len(unique_ads)} ads")

    processed = []
    for ad in unique_ads:
        start_date = get_ad_start_date(ad)
        if not start_date:
            continue

        days_running = (TODAY - start_date).days
        if days_running < MIN_DAYS_RUNNING:
            continue

        image_url = get_image_url(ad)
        if not image_url:
            continue

        img_hash = hashlib.md5(image_url.encode()).hexdigest()[:12]
        ext = ".jpg"
        if ".png" in image_url.lower():
            ext = ".png"
        elif ".webp" in image_url.lower():
            ext = ".webp"
        img_filename = f"ad_{img_hash}{ext}"

        processed.append({
            "brand": get_brand_name(ad),
            "text": get_ad_text(ad),
            "image_url": image_url,
            "image_file": img_filename,
            "start_date": start_date.isoformat(),
            "days_running": days_running,
        })

    print(f"After filtering (30+ days, has image): {len(processed)} ads")
    return processed


def download_all_images(ads: list):
    """Download all ad images in parallel."""
    print(f"\nDownloading {len(ads)} images...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(download_image, ad["image_url"], ad["image_file"]): ad
            for ad in ads
        }
        done = 0
        for future in as_completed(futures):
            done += 1
            if done % 10 == 0:
                print(f"  Downloaded {done}/{len(ads)}...")
    print(f"  Done downloading images.")


def build_gallery_html(ads: list):
    """Build the dark-themed HTML gallery."""
    brands = set(ad["brand"] for ad in ads)
    total_ads = len(ads)
    total_brands = len(brands)

    cards_html = ""
    for ad in sorted(ads, key=lambda x: -x["days_running"]):
        escaped_text = (
            ad["text"]
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("\n", "<br>")
        )
        escaped_brand = ad["brand"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        cards_html += f"""
        <div class="ad-card">
            <div class="badge">30+ days</div>
            <div class="ad-image-container">
                <img src="images/{ad['image_file']}" alt="Ad by {escaped_brand}" loading="lazy"
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22300%22%3E%3Crect fill=%22%23222%22 width=%22400%22 height=%22300%22/%3E%3Ctext fill=%22%234ade80%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 font-size=%2218%22%3EImage unavailable%3C/text%3E%3C/svg%3E'">
            </div>
            <div class="ad-content">
                <div class="brand-name">{escaped_brand}</div>
                <div class="days-running">{ad['days_running']} days running</div>
                <div class="ad-text">{escaped_text}</div>
                <div class="start-date">Started: {ad['start_date']}</div>
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meta Ad Library Gallery - 30+ Day Runners</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: #0a0a0a;
            color: #e0e0e0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
        }}
        .header {{
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            border-bottom: 1px solid #4ade80;
            padding: 2rem;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2rem;
            color: #4ade80;
            margin-bottom: 0.5rem;
            letter-spacing: -0.5px;
        }}
        .header .subtitle {{
            color: #888;
            font-size: 0.95rem;
        }}
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 3rem;
            padding: 1.5rem 2rem;
            background: #111;
            border-bottom: 1px solid #222;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #4ade80;
        }}
        .stat-label {{
            font-size: 0.8rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 0.25rem;
        }}
        .filter-bar {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            padding: 1rem 2rem;
            background: #0f0f0f;
            border-bottom: 1px solid #1a1a1a;
            flex-wrap: wrap;
        }}
        .filter-bar input {{
            background: #1a1a1a;
            border: 1px solid #333;
            color: #e0e0e0;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
            width: 300px;
            outline: none;
            transition: border-color 0.2s;
        }}
        .filter-bar input:focus {{
            border-color: #4ade80;
        }}
        .filter-bar select {{
            background: #1a1a1a;
            border: 1px solid #333;
            color: #e0e0e0;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
            outline: none;
            cursor: pointer;
        }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 1.5rem;
            padding: 2rem;
            max-width: 1600px;
            margin: 0 auto;
        }}
        .ad-card {{
            background: #141414;
            border: 1px solid #222;
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
            position: relative;
        }}
        .ad-card:hover {{
            transform: translateY(-4px);
            border-color: #4ade80;
            box-shadow: 0 8px 30px rgba(74, 222, 128, 0.1);
        }}
        .badge {{
            position: absolute;
            top: 12px;
            right: 12px;
            background: rgba(74, 222, 128, 0.15);
            color: #4ade80;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            z-index: 2;
            border: 1px solid rgba(74, 222, 128, 0.3);
            backdrop-filter: blur(8px);
        }}
        .ad-image-container {{
            width: 100%;
            aspect-ratio: 4/3;
            overflow: hidden;
            background: #1a1a1a;
        }}
        .ad-image-container img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s;
        }}
        .ad-card:hover .ad-image-container img {{
            transform: scale(1.03);
        }}
        .ad-content {{
            padding: 1.25rem;
        }}
        .brand-name {{
            font-weight: 700;
            font-size: 1.05rem;
            color: #fff;
            margin-bottom: 0.35rem;
        }}
        .days-running {{
            color: #4ade80;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        }}
        .ad-text {{
            color: #aaa;
            font-size: 0.88rem;
            line-height: 1.5;
            max-height: 4.5em;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            margin-bottom: 0.75rem;
        }}
        .start-date {{
            color: #555;
            font-size: 0.78rem;
        }}
        .no-results {{
            text-align: center;
            padding: 4rem 2rem;
            color: #555;
            font-size: 1.1rem;
        }}
        @media (max-width: 768px) {{
            .stats-bar {{
                gap: 1.5rem;
            }}
            .stat-value {{
                font-size: 1.5rem;
            }}
            .gallery {{
                grid-template-columns: 1fr;
                padding: 1rem;
            }}
            .header h1 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Meta Ad Library - Proven Ads Gallery</h1>
        <div class="subtitle">Active ads running 30+ days | IMAGE ads only | Scraped via Apify</div>
    </div>

    <div class="stats-bar">
        <div class="stat">
            <div class="stat-value">{total_ads}</div>
            <div class="stat-label">Total Ads</div>
        </div>
        <div class="stat">
            <div class="stat-value">{total_brands}</div>
            <div class="stat-label">Brands</div>
        </div>
        <div class="stat">
            <div class="stat-value">{TODAY.strftime('%b %d, %Y')}</div>
            <div class="stat-label">Scraped Date</div>
        </div>
    </div>

    <div class="filter-bar">
        <input type="text" id="searchInput" placeholder="Search by brand or ad text..." onkeyup="filterAds()">
        <select id="sortSelect" onchange="sortAds()">
            <option value="days-desc">Longest Running First</option>
            <option value="days-asc">Newest First</option>
            <option value="brand-asc">Brand A-Z</option>
        </select>
    </div>

    <div class="gallery" id="gallery">
        {cards_html}
    </div>

    <div class="no-results" id="noResults" style="display:none;">No ads match your search.</div>

    <script>
        function filterAds() {{
            const query = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.ad-card');
            let visible = 0;
            cards.forEach(card => {{
                const brand = card.querySelector('.brand-name').textContent.toLowerCase();
                const text = card.querySelector('.ad-text').textContent.toLowerCase();
                const match = brand.includes(query) || text.includes(query);
                card.style.display = match ? '' : 'none';
                if (match) visible++;
            }});
            document.getElementById('noResults').style.display = visible === 0 ? '' : 'none';
        }}

        function sortAds() {{
            const gallery = document.getElementById('gallery');
            const cards = Array.from(gallery.querySelectorAll('.ad-card'));
            const sort = document.getElementById('sortSelect').value;
            cards.sort((a, b) => {{
                if (sort === 'days-desc') {{
                    return parseInt(b.querySelector('.days-running').textContent) - parseInt(a.querySelector('.days-running').textContent);
                }} else if (sort === 'days-asc') {{
                    return parseInt(a.querySelector('.days-running').textContent) - parseInt(b.querySelector('.days-running').textContent);
                }} else {{
                    return a.querySelector('.brand-name').textContent.localeCompare(b.querySelector('.brand-name').textContent);
                }}
            }});
            cards.forEach(card => gallery.appendChild(card));
        }}
    </script>
</body>
</html>"""

    output_path = OUTPUT_DIR / "index.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"\nGallery saved to {output_path}")


def main():
    if not APIFY_TOKEN:
        print("ERROR: APIFY_API_TOKEN environment variable not set.")
        print("Usage: export APIFY_API_TOKEN='your_token' && python3 scrape_meta_ads.py")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)

    # Scrape ads
    all_ads = []
    for term in SEARCH_TERMS:
        for country in COUNTRIES:
            results = run_apify_actor(term, country)
            all_ads.extend(results)

    print(f"\nTotal raw results: {len(all_ads)}")

    if not all_ads:
        print("No ads found. Check your Apify token and search terms.")
        sys.exit(1)

    # Save raw data
    raw_path = OUTPUT_DIR / "raw_ads.json"
    with open(raw_path, "w") as f:
        json.dump(all_ads, f, indent=2, default=str)
    print(f"Raw data saved to {raw_path}")

    # Process and filter
    processed_ads = process_ads(all_ads)

    if not processed_ads:
        print("No ads passed the 30+ day filter.")
        sys.exit(1)

    # Save processed data
    proc_path = OUTPUT_DIR / "processed_ads.json"
    with open(proc_path, "w") as f:
        json.dump(processed_ads, f, indent=2)
    print(f"Processed data saved to {proc_path}")

    # Download images
    download_all_images(processed_ads)

    # Build gallery
    build_gallery_html(processed_ads)
    print("\nDone! Open ad-gallery/index.html in your browser.")


if __name__ == "__main__":
    main()
