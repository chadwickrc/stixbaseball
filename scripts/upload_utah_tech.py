"""
Retry upload for Utah Tech headshots with real error checking.
Re-uploads all files in headshots/ matching utah_tech_*.
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
    # Load Utah Tech players
    players_resp = sb.table("players").select("id, name").eq("school_id", "utah_tech").execute()
    players = players_resp.data
    lookup = {slugify(p["name"]): p["id"] for p in players}
    print(f"Loaded {len(players)} Utah Tech players")

    files = sorted([f for f in HEADSHOT_DIR.iterdir()
                    if f.is_file() and f.name.startswith("utah_tech_")
                    and f.suffix.lower() in CONTENT_TYPES])
    print(f"Found {len(files)} Utah Tech image files\n")

    uploaded = 0
    failed = 0

    for f in files:
        stem = f.stem  # e.g. utah_tech_mays-madsen
        slug = stem[len("utah_tech_"):]  # "mays-madsen"
        player_id = lookup.get(slug)

        if not player_id:
            print(f"  NO MATCH for {f.name}")
            failed += 1
            continue

        storage_path = f.name
        content_type = CONTENT_TYPES[f.suffix.lower()]
        file_size = f.stat().st_size

        try:
            with f.open("rb") as fh:
                result = sb.storage.from_(BUCKET).upload(
                    path=storage_path,
                    file=fh,
                    file_options={
                        "content-type": content_type,
                        "upsert": "true",
                    },
                )
            # Verify upload actually worked by listing
            listed = sb.storage.from_(BUCKET).list("", {"search": storage_path})
            if not listed:
                print(f"  UPLOAD FAILED (not visible after) for {f.name} ({file_size} bytes)")
                failed += 1
                continue

            public_url = sb.storage.from_(BUCKET).get_public_url(storage_path).rstrip("?")
            sb.table("players").update({"headshot_url": public_url}).eq("id", player_id).execute()
            uploaded += 1
            print(f"  OK: {f.name} ({file_size} bytes)")
        except Exception as e:
            print(f"  EXCEPTION for {f.name}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n=== Done ===")
    print(f"  Uploaded: {uploaded}")
    print(f"  Failed: {failed}")


if __name__ == "__main__":
    main()
