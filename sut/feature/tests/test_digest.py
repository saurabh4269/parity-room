from pathlib import Path

from weekly_report.digest import bucket_by_day, stamp
from weekly_report.events import load_events
from weekly_report.settings import load_settings

DATA = Path(__file__).resolve().parent.parent / "data" / "events.csv"


def test_load_settings():
    assert load_settings()["team"] == "platform"


def test_stamp_is_utc_iso():
    s = stamp()
    assert len(s) == 20 and s.endswith("Z")


def test_bucket_by_day():
    # expected values captured on the author's machine
    assert bucket_by_day(load_events(DATA)) == {"2024-11-01": 2, "2024-11-02": 2}
