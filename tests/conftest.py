import asyncio
from datetime import datetime
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from venvalid.dotenv import load_env_file

load_env_file(str(Path(__file__).with_name(".env.test")), override=True)

from main import app  # noqa: E402
from umami_report import umami  # noqa: E402


def fake_umami_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/stats"):
        return httpx.Response(200, json={"pageviews": {"value": 30, "prev": 1}, "visitors": 7, "visits": 9})
    metric_type = request.url.params["type"]
    if metric_type == "path":
        return httpx.Response(400)  # Simulates Umami v2, exercising the "url" fallback.
    metrics = {
        "country": [{"x": "BR", "y": 5}, {"x": None, "y": 2}],
        "device": [{"x": "mobile", "y": 6}, {"x": "desktop", "y": 1}],
        "url": [{"x": "/", "y": 20}, {"x": "/blog/a-very-long-route-name-here", "y": 10}],
    }
    return httpx.Response(200, json=metrics[metric_type])


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def report_period() -> tuple[datetime, datetime]:
    return datetime(2026, 10, 19), datetime(2026, 10, 26)


@pytest.fixture
def website() -> dict:
    return {"id": "abc", "name": "Site", "domain": "site.com"}


@pytest.fixture
def site_report(website: dict, report_period: tuple[datetime, datetime]) -> umami.SiteReport:
    start, end = report_period

    async def fetch() -> umami.SiteReport:
        transport = httpx.MockTransport(fake_umami_handler)
        async with httpx.AsyncClient(base_url="http://umami", transport=transport) as client:
            return await umami.fetch_site_report(client, website, start, end)

    return asyncio.run(fetch())


@pytest.fixture
def site_reports() -> list[umami.SiteReport]:
    return [
        umami.SiteReport(
            name="Blog",
            domain="blog.com",
            visits=10,
            visitors=8,
            pageviews=40,
            countries=[("BR", 6), ("US", 2)],
            devices=[("mobile", 5), ("desktop", 3)],
            routes=[("/", 25), ("/posts", 15)],
        ),
        umami.SiteReport(
            name="Shop",
            domain="shop.com",
            visits=20,
            visitors=12,
            pageviews=60,
            countries=[("US", 10), ("BR", 2)],
            devices=[("desktop", 12)],
            routes=[("/", 30), ("/cart", 20), ("/checkout", 10)],
        ),
    ]
