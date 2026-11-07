"""Load team settings from config/settings.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_settings():
    with open(ROOT / "config" / "Settings.json", encoding="utf-8") as fh:
        return json.load(fh)
