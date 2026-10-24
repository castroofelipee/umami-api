from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from umami_report.discord import build_report_embed, render_table
from umami_report.scheduler import next_run
from umami_report.umami import SiteReport


@pytest.mark.parametrize(
    ("after", "expected"),
    [
        (datetime(2026, 10, 21, 15, 0), datetime(2026, 10, 26, 9, 0)),  # Wednesday -> next Monday
        (datetime(2026, 10, 26, 8, 0), datetime(2026, 10, 26, 9, 0)),  # Monday before the hour -> same day
        (datetime(2026, 10, 26, 9, 0), datetime(2026, 11, 2, 9, 0)),  # Exactly on the slot -> a full week later
    ],
)
def test_next_run(after: datetime, expected: datetime):
    assert next_run(after, weekday=0, hour=9) == expected
