from pathlib import Path

from weekly_report.events import load_events

DATA = Path(__file__).resolve().parent.parent / "data" / "events.csv"


def test_load_events_reads_all_rows():
    events = load_events(DATA)
    assert len(events) == 4
    assert {e["actor"] for e in events} == {"priya", "sam", "maya"}
