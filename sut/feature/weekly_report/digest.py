"""Build the weekly digest."""
import datetime
from collections import Counter


def stamp():
    """ISO-8601 UTC timestamp for the report footer."""
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def bucket_by_day(events):
    """Count events per calendar day."""
    days = Counter()
    for ev in events:
        days[datetime.datetime.fromtimestamp(ev["ts"]).date().isoformat()] += 1
    return dict(sorted(days.items()))


def render(events, settings):
    lines = [f"# {settings['title']}", ""]
    for day, n in bucket_by_day(events).items():
        lines.append(f"- {day}: {n} events")
    lines += ["", f"_generated {stamp()}_"]
    return "\n".join(lines)
