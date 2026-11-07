"""Load team events from CSV (columns: ts,actor,kind)."""
import csv
from pathlib import Path


def load_events(path):
    with open(Path(path), newline="", encoding="utf-8") as fh:
        return [
            {"ts": float(row["ts"]), "actor": row["actor"], "kind": row["kind"]}
            for row in csv.DictReader(fh)
        ]
