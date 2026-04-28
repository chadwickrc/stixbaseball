"""
Seed the bats and gloves tables with popular models used in NCAA D1 baseball.

Idempotent: skips rows whose (brand, model) already exists, so re-running is safe.
All bats are BBCOR -3 with 2 5/8" barrel (NCAA standard). Length set to 33"
as the most common college length; variants can be added as separate rows later.

Glove rows capture one canonical config per (brand, model). Specific size/web
variants can be added later when sightings demand them.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    sys.exit(1)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)


BATS = [
    # Marucci
    {"brand": "Marucci", "model": "CAT X Connect", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Red"},
    {"brand": "Marucci", "model": "CAT X", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Red"},
    {"brand": "Marucci", "model": "CAT 9 Connect", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Red"},
    {"brand": "Marucci", "model": "Posey 28 Pro Metal", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Gold"},
    # Louisville Slugger
    {"brand": "Louisville Slugger", "model": "Meta", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Red"},
    {"brand": "Louisville Slugger", "model": "Atlas", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Silver"},
    {"brand": "Louisville Slugger", "model": "Select PWR", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Red"},
    # DeMarini
    {"brand": "DeMarini", "model": "The Goods (One-Piece)", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Gold"},
    {"brand": "DeMarini", "model": "The Goods Two-Piece", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Gold"},
    {"brand": "DeMarini", "model": "Voodoo One", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Red"},
    {"brand": "DeMarini", "model": "ZOA", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Yellow"},
    # Easton
    {"brand": "Easton", "model": "Hype Fire", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Red"},
    {"brand": "Easton", "model": "Hype Comp", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Yellow"},
    # Rawlings
    {"brand": "Rawlings", "model": "Icon", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Red"},
    {"brand": "Rawlings", "model": "Quatro Pro", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Silver"},
    # Victus
    {"brand": "Victus", "model": "Vandal", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Gold"},
    {"brand": "Victus", "model": "NOX", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Matte Black"},
    # Axe
    {"brand": "Axe", "model": "Avenge Pro", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/Red"},
    {"brand": "Axe", "model": "Elite One", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black/White"},
    # True
    {"brand": "True", "model": "T1", "length_in": 33, "weight_drop": -3, "barrel_size": 2.625, "bbcor": True, "colorway": "Black"},
]


GLOVES = [
    # Rawlings
    {"brand": "Rawlings", "model": "Heart of the Hide", "size_in": "11.5", "web_type": "I-Web", "position_type": "infield", "colorway": "Tan/Black"},
    {"brand": "Rawlings", "model": "Pro Preferred", "size_in": "11.75", "web_type": "Modified Trap", "position_type": "infield", "colorway": "Black/Tan"},
    {"brand": "Rawlings", "model": "Gold Glove", "size_in": "12", "web_type": "Two-Piece Solid", "position_type": "pitcher", "colorway": "Tan"},
    {"brand": "Rawlings", "model": "R2G Heart of the Hide", "size_in": "11.5", "web_type": "I-Web", "position_type": "infield", "colorway": "Tan"},
    # Wilson
    {"brand": "Wilson", "model": "A2000 1786", "size_in": "11.5", "web_type": "H-Web", "position_type": "infield", "colorway": "Black/Tan"},
    {"brand": "Wilson", "model": "A2000 SuperSkin 1787", "size_in": "11.75", "web_type": "H-Web", "position_type": "infield", "colorway": "Black/Grey"},
    {"brand": "Wilson", "model": "A2K DP15", "size_in": "11.5", "web_type": "I-Web", "position_type": "infield", "colorway": "Tan/Black"},
    {"brand": "Wilson", "model": "A2K B2", "size_in": "12", "web_type": "Two-Piece Solid", "position_type": "pitcher", "colorway": "Tan"},
    # Mizuno
    {"brand": "Mizuno", "model": "Pro", "size_in": "11.5", "web_type": "I-Web", "position_type": "infield", "colorway": "Tan/Black"},
    {"brand": "Mizuno", "model": "Classic Pro Soft", "size_in": "12.75", "web_type": "T-Web", "position_type": "outfield", "colorway": "Brown"},
    # Marucci
    {"brand": "Marucci", "model": "Magnus", "size_in": "11.5", "web_type": "I-Web", "position_type": "infield", "colorway": "Tan/Black"},
    {"brand": "Marucci", "model": "Capitol Series", "size_in": "11.75", "web_type": "Modified Trap", "position_type": "infield", "colorway": "Black/Tan"},
    # Nokona
    {"brand": "Nokona", "model": "Walnut", "size_in": "11.5", "web_type": "I-Web", "position_type": "infield", "colorway": "Walnut"},
    {"brand": "Nokona", "model": "Alpha", "size_in": "11.75", "web_type": "H-Web", "position_type": "infield", "colorway": "Brown"},
    # Easton
    {"brand": "Easton", "model": "Pro Collection", "size_in": "11.5", "web_type": "I-Web", "position_type": "infield", "colorway": "Black/Tan"},
]


def seed_table(name, rows, key_fields):
    existing = sb.table(name).select(",".join(key_fields)).execute().data
    existing_keys = {tuple(row[f] for f in key_fields) for row in existing}

    to_insert = [r for r in rows if tuple(r[f] for f in key_fields) not in existing_keys]
    skipped = len(rows) - len(to_insert)

    if to_insert:
        sb.table(name).insert(to_insert).execute()

    print(f"{name}: inserted {len(to_insert)}, skipped {skipped} (already present)")


def main():
    seed_table("bats", BATS, ["brand", "model"])
    seed_table("gloves", GLOVES, ["brand", "model"])
    print("Done.")


if __name__ == "__main__":
    main()
