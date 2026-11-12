from __future__ import annotations

from datetime import datetime, timezone


def parse_instant(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    moment = datetime.fromisoformat(text)
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
