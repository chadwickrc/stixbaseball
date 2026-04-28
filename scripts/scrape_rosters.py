"""
Utah college baseball roster scraper v3.
Header-aware parsing with substring matching. Four schools, four layouts:
  - Utah (SIDEARM): 10 cols including Academic Major
  - BYU (custom CMS): 8 cols, no Wt, no B/T column (B/T embedded in position),
    "Previous School" is really the high school for freshmen / last school for transfers
  - Utah Valley (SIDEARM): 9 cols, "Hometown / High School" combined
  - Utah Tech (SIDEARM): 10 cols, extra Image col, separate CL column
Output: rosters.csv
"""

import csv
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SCHOOLS = [
    {"school_id": "utah", "school_name": "Utah",
     "roster_url": "https://utahutes.com/sports/baseball/roster",
     "base_url": "https://utahutes.com", "parser": "sidearm"},
    {"school_id": "byu", "school_name": "BYU",
     "roster_url": "https://byucougars.com/sports/baseball/roster",
     "base_url": "https://byucougars.com", "parser": "byu"},
    {"school_id": "uvu", "school_name": "Utah Valley",
     "roster_url": "https://gouvu.com/sports/baseball/roster",
     "base_url": "https://gouvu.com", "parser": "sidearm"},
    {"school_id": "utah_tech", "school_name": "Utah Tech",
     "roster_url": "https://utahtechtrailblazers.com/sports/baseball/roster",
     "base_url": "https://utahtechtrailblazers.com", "parser": "sidearm"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class Player:
    school_id: str
    school_name: str
    jersey: str
    name: str
    position: str
    bats: str
    throws: str
    height: str
    weight: str
    class_year: str
    hometown: str
    high_school: str
    previous_school: str
    profile_url: str
    headshot_url: str


def fetch(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def clean(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def split_bt(raw):
    if not raw or "/" not in raw:
        return ("", "")
    parts = raw.split("/", 1)
    return (parts[0].strip(), parts[1].strip())


def split_hometown(raw):
    if not raw:
        return ("", "")
    if "/" in raw:
        parts = raw.split("/", 1)
        return (parts[0].strip(), parts[1].strip())
    return (raw.strip(), "")


# Substring-based header matching. Order matters: more specific strings first.
# Each entry: (substring-to-find-in-lowercased-header, canonical-field-name)
HEADER_PATTERNS = [
    ("hometown / high school", "hometown_hs"),
    ("hometown/high school", "hometown_hs"),
    ("academic major", "skip"),   # explicitly drop
    ("major", "skip"),
    ("connect", "skip"),           # BYU social media column
    ("image", "skip"),             # Utah Tech photo column
    ("jersey number", "jersey"),   # BYU's weird concatenated header
    ("number", "jersey"),
    ("full name", "name"),
    ("name", "name"),
    ("pos", "position"),
    ("position", "position"),
    ("b/t", "bt"),
    ("bats/throws", "bt"),
    ("ht", "height"),
    ("height", "height"),
    ("wt", "weight"),
    ("weight", "weight"),
    ("yr", "class_year"),
    ("year", "class_year"),
    ("class", "class_year"),
    ("cl", "class_year"),
    ("hometown", "hometown"),
    ("high school", "high_school"),
    ("previous school", "previous_school"),
    ("previous", "previous_school"),
    ("last school", "previous_school"),
    ("#", "jersey"),  # keep last so longer patterns win
]


def classify_header(text):
    t = text.lower().strip().rstrip(".")
    # Collapse BYU's weird duplicate label "numberjersey number" -> we match on substring so this works
    for pattern, field in HEADER_PATTERNS:
        if pattern in t:
            return field
    return None


def build_column_map(header_row):
    cells = header_row.find_all(["th", "td"])
    col_map = {}
    for i, cell in enumerate(cells):
        text = clean(cell.get_text())
        field = classify_header(text)
        if field and field != "skip":
            col_map[i] = field
    return col_map


def find_roster_table(soup):
    for table in soup.find_all("table"):
        header_text = clean(table.get_text(" ", strip=True))[:300].lower()
        if "name" in header_text and ("hometown" in header_text or "previous" in header_text):
            return table
    return None


def parse_sidearm(html, school):
    soup = BeautifulSoup(html, "lxml")
    players = []
    table = find_roster_table(soup)
    if table is None:
        print(f"  !! no roster table found for {school['school_name']}")
        return players

    header_row = None
    thead = table.find("thead")
    if thead:
        header_row = thead.find("tr")
    if header_row is None:
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if cells and all(c.name == "th" for c in cells):
                header_row = tr
                break
    if header_row is None:
        print(f"  !! no header row found for {school['school_name']}")
        return players

    col_map = build_column_map(header_row)
    if not col_map:
        print(f"  !! could not map columns for {school['school_name']}")
        return players

    body = table.find("tbody")
    data_rows = body.find_all("tr") if body else table.find_all("tr")

    for row in data_rows:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        if all(c.name == "th" for c in cells):
            continue

        values = {}
        for idx, cell in enumerate(cells):
            field = col_map.get(idx)
            if not field:
                continue
            if field == "name":
                values["name"] = clean(cell.get_text())
                link = cell.find("a")
                if link and link.get("href"):
                    href = link["href"]
                    values["profile_url"] = href if href.startswith("http") else school["base_url"] + href
            else:
                values[field] = clean(cell.get_text())

        if not values.get("name"):
            continue

        bats, throws = split_bt(values.get("bt", ""))

        # Handle the Hometown/HS combined column OR separate columns
        hometown_hs = values.get("hometown_hs", "")
        if hometown_hs:
            hometown, high_school = split_hometown(hometown_hs)
        else:
            hometown = values.get("hometown", "")
            high_school = values.get("high_school", "")

        players.append(Player(
            school_id=school["school_id"],
            school_name=school["school_name"],
            jersey=values.get("jersey", ""),
            name=values.get("name", ""),
            position=values.get("position", ""),
            bats=bats,
            throws=throws,
            height=values.get("height", ""),
            weight=values.get("weight", ""),
            class_year=values.get("class_year", ""),
            hometown=hometown,
            high_school=high_school,
            previous_school=values.get("previous_school", ""),
            profile_url=values.get("profile_url", ""),
            headshot_url="",
        ))
    return players


BT_IN_PAREN = re.compile(r"\(([LRS])\s*/\s*([LRS])\)")


def parse_byu(html, school):
    """
    BYU special cases:
      - position string contains B/T in parens: 'Outfielder (L/L)'
      - "Previous School" column actually contains the player's high school (or last college for transfers)
        BYU's labeling convention. We store that value in high_school rather than previous_school.
    """
    players = parse_sidearm(html, school)
    for p in players:
        # Extract B/T from position
        m = BT_IN_PAREN.search(p.position)
        if m:
            p.bats = m.group(1)
            p.throws = m.group(2)
            p.position = clean(BT_IN_PAREN.sub("", p.position))

        # BYU's "Previous School" is really the high school / last-school label.
        # Move it to high_school if high_school is empty.
        if p.previous_school and not p.high_school:
            p.high_school = p.previous_school
            p.previous_school = ""
    return players


PARSERS = {"sidearm": parse_sidearm, "byu": parse_byu}


def scrape_all():
    all_players = []
    for school in SCHOOLS:
        print(f"Fetching {school['school_name']} ({school['roster_url']}) ...")
        try:
            html = fetch(school["roster_url"])
        except Exception as e:
            print(f"  !! failed: {e}")
            continue
        parser = PARSERS.get(school.get("parser", "sidearm"), parse_sidearm)
        players = parser(html, school)
        print(f"  got {len(players)} players")
        all_players.extend(players)
        time.sleep(1)
    return all_players


def write_csv(players, path):
    if not players:
        return
    fieldnames = list(asdict(players[0]).keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in players:
            writer.writerow(asdict(p))


def summarize(players):
    if not players:
        print("\nNo players scraped.")
        return
    print(f"\n=== Summary: {len(players)} total players ===")
    by_school = {}
    for p in players:
        by_school[p.school_name] = by_school.get(p.school_name, 0) + 1
    for school, count in sorted(by_school.items()):
        print(f"  {school}: {count}")
    print("\nSample rows (one per school):")
    seen = set()
    for p in players:
        if p.school_name in seen:
            continue
        seen.add(p.school_name)
        print(f"  [{p.school_name} #{p.jersey}] {p.name} | pos={p.position} | B/T={p.bats}/{p.throws} | yr={p.class_year} | ht={p.height} | wt={p.weight}")
        print(f"    hometown={p.hometown} | hs={p.high_school} | prev={p.previous_school}")


if __name__ == "__main__":
    out = Path(__file__).parent / "rosters.csv"
    players = scrape_all()
    if players:
        write_csv(players, out)
        print(f"\nWrote {out}")
    summarize(players)
