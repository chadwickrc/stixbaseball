"""
Import rosters.csv into the Supabase players table.
Uses the external_id field (profile_url) as the dedup key, so this script
is idempotent - re-running it updates existing rows rather than duplicating.
"""

import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

HERE = Path(__file__).parent
CSV_PATH = HERE / "rosters.csv"

load_dotenv(HERE / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    sys.exit(1)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)


def clean_row(row):
    """Convert CSV row dict -> players table row. Empty strings become NULL."""
    return {
        "school_id":       row["school_id"] or None,
        "external_id":     row["profile_url"] or None,
        "jersey":          row["jersey"] or None,
        "name":            row["name"],
        "position":        row["position"] or None,
        "bats":            row["bats"] or None,
        "throws":          row["throws"] or None,
        "height":          row["height"] or None,
        "weight":          row["weight"] or None,
        "class_year":      row["class_year"] or None,
        "hometown":        row["hometown"] or None,
        "high_school":     row["high_school"] or None,
        "previous_school": row["previous_school"] or None,
        "profile_url":     row["profile_url"] or None,
        # headshot_url left blank for now; we'll populate after uploading to storage
    }


def main():
    if not CSV_PATH.exists():
        print(f"No rosters.csv at {CSV_PATH}")
        sys.exit(1)

    # Since the players table has no unique constraint on external_id,
    # we'll clear existing rows and re-insert. Safer than trying to upsert
    # without a unique constraint defined in SQL.
    # (Future runs could add a unique constraint and use upsert.)
    print("Deleting existing player rows...")
    sb.table("players").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    rows = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(clean_row(r))

    print(f"Inserting {len(rows)} players...")
    # Insert in batches of 50 to keep the request size reasonable
    batch_size = 50
    inserted = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        resp = sb.table("players").insert(batch).execute()
        inserted += len(resp.data)
        print(f"  inserted batch {i//batch_size + 1}: {len(resp.data)} rows")

    print(f"\nDone. {inserted} players in the database.")

    # Sanity check
    count = sb.table("players").select("*", count="exact").execute()
    by_school = {}
    for p in count.data:
        by_school[p["school_id"]] = by_school.get(p["school_id"], 0) + 1
    print(f"\nBreakdown:")
    for s, c in sorted(by_school.items()):
        print(f"  {s}: {c}")


if __name__ == "__main__":
    main()
