# Utah College Baseball Gear Tracker — Project Handoff

**Last updated:** April 28, 2026

Paste this doc at the start of any new Claude conversation to get full context.

**Live site:** https://stixbaseball.vercel.app
**GitHub:** https://github.com/chadwickrc/stixbaseball (public, auto-deploys on push to main)

---

## What this is

A kixstats.com-style site for Utah D1 college baseball. Tracks which bats, gloves, and other gear each player uses, tied to their stats and team. Inspired by kixstats which does this for NBA sneakers.

**Current scope (v1):** Four Utah D1 programs (Utah, BYU, Utah Valley, Utah Tech), bats + gloves only. Expand from there.

**Stated goal:** Real site that people actually use and visit, not a personal toy project.

---

## Tech stack

- **Frontend:** Next.js 16.2.4 with App Router, TypeScript, Tailwind CSS, React 19
- **Database:** Supabase (Postgres + Storage + Auth)
- **Scraping:** Python 3 with requests + BeautifulSoup + lxml
- **Deployment target:** Vercel (not yet deployed, still local)
- **Node:** v24 (cutting edge but working)

---

## File layout

```
~/kixbaseball/                       (Next.js app, root of the web project)
├── app/
│   ├── page.tsx                     Homepage: grid of 4 schools
│   ├── schools/[schoolId]/page.tsx  School page: roster grid with headshots
│   └── players/[playerId]/page.tsx  Player detail: big headshot + bio + gear placeholder
├── lib/
│   └── supabase.ts                  Supabase client + TS types for School and Player
├── scripts/                         (Python data pipeline, lives inside the Next.js project)
│   ├── .venv/                       Virtual environment (gitignored)
│   ├── .env                         SUPABASE_URL + SUPABASE_SERVICE_KEY (local only!)
│   ├── scrape_rosters.py            Pulls rosters from all 4 schools, outputs rosters.csv
│   ├── scrape_headshots.py          Downloads headshots to headshots/, updates CSV
│   ├── import_players.py            Imports rosters.csv into Supabase players table
│   ├── upload_headshots.py          Uploads headshots/ to Supabase Storage + links to players
│   ├── upload_utah_tech.py          Targeted version of upload_headshots for just Utah Tech (with better error handling)
│   ├── rosters.csv                  147 players, all fields populated
│   └── headshots/                   111 local image files (utah_*, uvu_*, utah_tech_*)
├── next.config.ts                   (has Supabase storage hostname allowlisted for next/image)
├── .env.local                       NEXT_PUBLIC_SUPABASE_URL + NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
├── AGENTS.md                        Claude Code config
└── CLAUDE.md                        Claude Code config
```

**Important:** there are TWO env files:
- `~/kixbaseball/.env.local` — used by Next.js, contains the publishable key (safe to be public)
- `~/kixbaseball/scripts/.env` — used by Python, contains the service role key (must stay local)

---

## Supabase project details

- **Project URL:** `https://gyumcqneczqogmtjaaog.supabase.co`
- **Project ref:** `gyumcqneczqogmtjaaog`
- **Publishable key:** `sb_publishable_7HR1_vhEw2ekwxoElO45nw_zTF9-UVq` (safe to share)
- **Service role key:** stored in `scripts/.env` only, never share in chat

### Database schema (all tables exist, RLS enabled, public read allowed)

- `schools` (id text PK, name, short_name, conference, roster_url, stats_url, instagram) — seeded with 4 rows
- `players` (id uuid PK, school_id FK, external_id, jersey, name, position, bats, throws, height, weight, class_year, hometown, high_school, previous_school, profile_url, headshot_url, created_at, updated_at) — 147 rows
- `bats` (id uuid PK, brand, model, length_in, weight_drop, barrel_size, bbcor, colorway, image_url) — 20 rows seeded (popular NCAA BBCOR models, no images yet)
- `gloves` (id uuid PK, brand, model, size_in, web_type, position_type, colorway, image_url) — 15 rows seeded (one canonical config per brand/model, no images yet)
- `sightings` (id, player_id FK, gear_type check-constraint bat|glove, bat_id FK, glove_id FK, photo_url, photo_date, source, confidence check-constraint low|medium|high, confirmed, confirmed_at, notes) — empty, not yet seeded

### Storage

- Bucket `headshots` (public), contains 111 image files
- File naming convention: `<school_id>_<slugified-name>.<ext>`, e.g. `utah_colter-mcanelly.jpg`

---

## Data state

| School | Players | Headshots |
|---|---|---|
| Utah (utah) | 34 | 34 |
| BYU (byu) | 36 | 0 |
| Utah Valley (uvu) | 40 | 40 |
| Utah Tech (utah_tech) | 37 | 37 |
| **Total** | **147** | **111** |

BYU doesn't have headshots because their roster page uses JS-rendered lazy loading (image URLs are populated client-side). Skipped for v1. BYU also doesn't publish weights on their roster page, so the `weight` column is null for all BYU players.

---

## Scraper notes (for future maintenance)

Each school has its own HTML layout quirks. The scraper uses header-aware parsing to handle this:

- **Utah (SIDEARM):** 10 columns including Academic Major. Standard B/T column.
- **BYU (custom CMS):** 8 columns. No weight column. B/T is embedded in position field like "Outfielder (L/L)". "Previous School" column actually contains the player's high school. There's a "Connect" column with social media junk that gets dropped.
- **UVU (SIDEARM):** 9 columns. "Hometown / High School" combined into one column.
- **Utah Tech (SIDEARM):** 10 columns. Has an extra "Image" column at position 0, and a separate "CL" column for class year.

The parser reads each table's header row and builds a column map dynamically. To add a 5th school, just add to the `SCHOOLS` list in `scrape_rosters.py` and (if needed) extend the `HEADER_PATTERNS` list.

**Running the pipeline fresh:**

```bash
cd ~/kixbaseball/scripts
source .venv/bin/activate
python3 scrape_rosters.py           # creates/updates rosters.csv
python3 scrape_headshots.py         # downloads images, updates CSV with local paths
python3 import_players.py           # imports CSV to Supabase players table
python3 upload_headshots.py         # uploads images to Supabase Storage + links to players
python3 seed_gear.py                # seeds bats + gloves catalog (idempotent on brand+model)
```

Every script is idempotent (safe to re-run).

---

## What's built (working)

1. Roster data for 147 players across 4 schools in Supabase
2. 111 headshots in Supabase Storage, linked to player rows
3. Public site at `http://localhost:3002` (custom port because ccusage uses 3000):
   - Homepage showing 4 schools
   - School pages showing roster grid with photos, clickable player cards
   - Player detail pages with full bio and "Gear Used" placeholder

To run the dev server:
```bash
cd ~/kixbaseball
npm run dev -- --port 3002
```

---

## What's NOT built

1. **Gear catalog:** `bats` and `gloves` tables are empty. Need to seed ~20 bat models and ~15 glove models with images.
2. **Sighting pipeline:** The core value prop. Photo upload → Claude Vision identifies gear → admin review → link to player. Not started.
3. **Admin UI:** No way to approve sightings, add gear to catalog, etc.
4. **Stats integration:** Each school has a stats page we could scrape weekly during season. Not built.
5. **Instagram photo scraping:** Original plan was to pull photos from team IG accounts. Deferred because IG actively breaks scrapers. Should revisit with manual photo dumps first.
6. **Authentication:** Site is read-only public for now. Contributor auth needed eventually.
7. **Vercel deployment:** Still local-only. Needs Vercel account + GitHub repo + env vars set in Vercel dashboard.
8. **No git repo yet.** Project is not under version control. Should `git init` and push to GitHub before deploying.

---

## Known issues and gotchas

- **ccusage port collision:** Port 3000 is held by ccusage (Claude Code usage tracker). We use port 3002 instead.
- **BYU limitations:** No weights, no headshots, B/T embedded in position string. BYU parser is separate from SIDEARM parser in `scrape_rosters.py`.
- **Heredocs are fragile in zsh for large code blocks.** When pasting large files via `cat > file << 'EOF'`, long blocks can get truncated or mangled. Use `nano` as editor, or a real IDE (VS Code), for anything over ~50 lines.
- **TextEdit defaults to RTF.** Don't use TextEdit for code files. If you must, use Format → Make Plain Text FIRST.
- **Python dependencies need the venv activated:** `source .venv/bin/activate` in `scripts/` before running any Python script.
- **macOS externally-managed-environment error:** Homebrew's Python blocks global pip installs. Must use venv (already set up).

---

## Next session priorities (in order)

Pick from this list when continuing the project:

1. **Git init + VS Code setup** (~15 min, one-time). Prevents future paper cuts. Strongly recommended before more code work.
2. **Deploy to Vercel** (~15 min). Gets the site on a real public URL, which matters for the "people will actually use it" goal.
3. ~~**Seed the gear catalog**~~ ✅ done 2026-04-28 via `scripts/seed_gear.py` (20 bats, 15 gloves). Future: add image_url to each row, split popular models into size/position variants as sightings demand it.
4. **Sighting pipeline** (multi-session). The flywheel: photo → Claude Vision → review → publish. This is the heavy lift that makes the site valuable. **Up next.**
5. **Stats scraper** (~1 hour). Weekly scrape of each school's stats page, joined to players by name.
6. **Instagram photo collection** (variable). Manual dumps first, maybe Apify later.

---

## Things Ryan preferred during the build

- Candid, data-backed recommendations, not excessive hedging
- "Here's the hard truth" framing when a choice has tradeoffs
- No em dashes anywhere (use commas, periods, parentheses, colons)
- Single clear next step at the end of each response
- Bullet points for scannability, not walls of text
- Being told when to stop for the day rather than pushed to keep going
