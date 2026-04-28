"""
Headshot scraper for Utah college baseball v1.
Reads rosters.csv, revisits each school's roster page, extracts the image URL
associated with each player's profile link, and downloads images to ./headshots/.
Updates rosters.csv's headshot_url column with the local path.
BYU uses JS-rendered lazy loading, so we skip BYU for v1.
"""

import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

ROSTER_URLS = {
    "utah": ("https://utahutes.com/sports/baseball/roster", "https://utahutes.com"),
    "uvu": ("https://gouvu.com/sports/baseball/roster", "https://gouvu.com"),
    "utah_tech": ("https://utahtechtrailblazers.com/sports/baseball/roster", "https://utahtechtrailblazers.com"),
}

HERE = Path(__file__).parent
HEADSHOT_DIR = HERE / "headshots"
CSV_PATH = HERE / "rosters.csv"


def unwrap_sidearm_proxy(url):
    if "images.sidearmdev.com" in url and "url=" in url:
        m = re.search(r"[?&]url=([^&]+)", url)
        if m:
            return unquote(m.group(1))
    return url


def strip_query(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def build_player_image_map(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    result = {}
    profile_re = re.compile(r"/sports/baseball/roster/[^/]+/\d+")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not profile_re.search(href):
            continue
        abs_href = href if href.startswith("http") else urljoin(base_url, href)
        if abs_href in result:
            continue

        candidate_img = None
        node = a
        for _ in range(6):
            parent = node.parent
            if parent is None:
                break
            img = parent.find("img")
            if img:
                candidate_img = img
                break
            node = parent

        if candidate_img is None:
            continue

        raw = candidate_img.get("src") or candidate_img.get("data-src") or ""
        if not raw:
            srcset = candidate_img.get("srcset", "")
            if srcset:
                raw = srcset.split(",")[0].strip().split(" ")[0]
        if not raw:
            continue

        if not raw.startswith("http"):
            raw = urljoin(base_url, raw)
        raw = unwrap_sidearm_proxy(raw)
        raw = strip_query(raw)

        lower = raw.lower()
        skip_markers = ("logo", "sponsor", "banner", "responsive_2024",
                        "footer", "nextgen_2024", "sidearm.nextgen.sites/images")
        if any(m in lower for m in skip_markers):
            continue

        result[abs_href] = raw

    return result


def download_image(url, dest):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"    failed to download {url}: {e}")
        return False
    dest.write_bytes(r.content)
    return True


def slugify(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def main():
    if not CSV_PATH.exists():
        print(f"No rosters.csv found at {CSV_PATH}. Run scrape_rosters.py first.")
        return

    HEADSHOT_DIR.mkdir(exist_ok=True)

    image_maps = {}
    for school_id, (roster_url, base_url) in ROSTER_URLS.items():
        print(f"Scanning {school_id} roster for images...")
        try:
            r = requests.get(roster_url, headers=HEADERS, timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"  failed: {e}")
            image_maps[school_id] = {}
            continue
        m = build_player_image_map(r.text, base_url)
        print(f"  found {len(m)} player images")
        image_maps[school_id] = m
        time.sleep(1)

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    downloaded = 0
    skipped_byu = 0
    missing = 0

    for row in rows:
        school_id = row["school_id"]
        if school_id == "byu":
            skipped_byu += 1
            continue

        image_map = image_maps.get(school_id, {})
        image_url = image_map.get(row["profile_url"], "")

        if not image_url:
            missing += 1
            print(f"  no image for {row['school_name']} #{row['jersey']} {row['name']}")
            continue

        ext = Path(urlparse(image_url).path).suffix.lower() or ".jpg"
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            ext = ".jpg"

        filename = f"{school_id}_{slugify(row['name'])}{ext}"
        dest = HEADSHOT_DIR / filename

        if dest.exists() and dest.stat().st_size > 1000:
            row["headshot_url"] = str(dest.relative_to(HERE))
            downloaded += 1
            continue

        if download_image(image_url, dest):
            row["headshot_url"] = str(dest.relative_to(HERE))
            downloaded += 1
            time.sleep(0.3)
        else:
            missing += 1

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n=== Done ===")
    print(f"  Downloaded/cached: {downloaded}")
    print(f"  Missing (no image found): {missing}")
    print(f"  Skipped (BYU, no JS): {skipped_byu}")
    print(f"  Files in {HEADSHOT_DIR}")


if __name__ == "__main__":
    main()
