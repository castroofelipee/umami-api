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


def test_site_report_reads_both_umami_shapes(site_report: SiteReport):
    assert (site_report.visits, site_report.visitors, site_report.pageviews) == (9, 7, 30)
    assert site_report.countries == [("BR", 5), ("(unknown)", 2)]
    assert site_report.routes[0] == ("/", 20)


def test_report_embed_sums_all_sites_in_one_table(
    site_reports: list[SiteReport], report_period: tuple[datetime, datetime]
):
    embed = build_report_embed(site_reports, *report_period, top_n=3)
    fields = {field["name"]: field["value"] for field in embed["fields"]}

    assert "│ Shop  │     20 │       12 │    60 │" in embed["description"]
    assert "│ Total │     30 │       20 │   100 │" in embed["description"]
    assert "│ Country │ Visitors │ Share │" in fields["🌍 Where from"]
    assert "│ US      │       12 │ 60.0% │" in fields["🌍 Where from"]
    assert "│ Desktop │       15 │ 75.0% │" in fields["💻 Devices"]
    assert "│ Shop │ /     │    30 │" in fields["🔥 Top routes"]
    assert "/checkout" not in fields["🔥 Top routes"]  # Only the top 3 routes across every site.
    assert all(len(value) <= 1024 for value in fields.values())  # Discord field limit


def test_render_table_aligns_columns():
    table = render_table(["Name", "Count"], [["a", "1"], ["long", "100"]])
    lines = table.splitlines()[1:-1]
    assert len({len(line) for line in lines}) == 1
    assert "│ a    │     1 │" in table


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_route_listings_hidden_in_production(api_client: TestClient, path: str):
    assert api_client.get(path).status_code == 404


def test_trigger_requires_token(api_client: TestClient):
    assert api_client.post("/reports/weekly", headers={"X-Trigger-Token": "anything"}).status_code == 403
