"""
Upload headshots/ folder contents to Supabase Storage,
then update each player's headshot_url column with the public URL.

Matches files to players by filename convention:
  headshots/<school_id>_<slug>.<ext>  e.g. headshots/utah_colter-mcanelly.jpg
Which corresponds to a unique (school_id, slugified name) in the players table.
"""

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

HERE = Path(__file__).parent
HEADSHOT_DIR = HERE / "headshots"
BUCKET = "headshots"

load_dotenv(HERE / ".env")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    sys.exit(1)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)


def slugify(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def main():
    if not HEADSHOT_DIR.exists():
        print(f"No headshots/ folder at {HEADSHOT_DIR}")
        sys.exit(1)

    # Pull all players so we can match filenames -> player ids
    players_resp = sb.table("players").select("id, school_id, name").execute()
    players = players_resp.data
    print(f"Loaded {len(players)} players from Supabase")

    # Build lookup: (school_id, slugified name) -> player_id
    lookup = {}
    for p in players:
        key = (p["school_id"], slugify(p["name"]))
        lookup[key] = p["id"]

    files = sorted(HEADSHOT_DIR.iterdir())
    files = [f for f in files if f.is_file() and f.suffix.lower() in CONTENT_TYPES]
    print(f"Found {len(files)} image files to upload")

    uploaded = 0
    matched = 0
    skipped = 0
    unmatched = []

    for f in files:
        # filename = <school_id>_<slug>.<ext>
        stem = f.stem
        ext = f.suffix.lower()
        parts = stem.split("_", 1)
        if len(parts) != 2:
            print(f"  skip (bad filename): {f.name}")
            skipped += 1
            continue
        school_id, slug = parts
        player_id = lookup.get((school_id, slug))
        if not player_id:
            unmatched.append(f.name)
            continue

        storage_path = f.name  # flat namespace inside the bucket
        content_type = CONTENT_TYPES[ext]

        # Upload (upsert=true so re-running overwrites)
        try:
            with f.open("rb") as fh:
                sb.storage.from_(BUCKET).upload(
                    path=storage_path,
                    file=fh,
                    file_options={
                        "content-type": content_type,
                        "upsert": "true",
                    },
                )
            uploaded += 1
        except Exception as e:
            print(f"  upload failed for {f.name}: {e}")
            continue

        # Get the public URL and update the player row
        public_url = sb.storage.from_(BUCKET).get_public_url(storage_path)
        # Supabase sometimes appends a trailing ?, strip it
        public_url = public_url.rstrip("?")

        sb.table("players").update({"headshot_url": public_url}).eq("id", player_id).execute()
        matched += 1

    print(f"\n=== Done ===")
    print(f"  Uploaded: {uploaded}")
    print(f"  Matched to player rows: {matched}")
    print(f"  Skipped (bad filename): {skipped}")
    if unmatched:
        print(f"  Unmatched files ({len(unmatched)}):")
        for name in unmatched[:10]:
            print(f"    {name}")
        if len(unmatched) > 10:
            print(f"    ... and {len(unmatched) - 10} more")


if __name__ == "__main__":
    main()
