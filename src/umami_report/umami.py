from dataclasses import dataclass
from datetime import datetime

import httpx


@dataclass
class SiteReport:
    name: str
    domain: str
    visits: int
    visitors: int
    pageviews: int
    countries: list[tuple[str, int]]
    devices: list[tuple[str, int]]
    routes: list[tuple[str, int]]


def read_stat(stat: dict | int | None) -> int:
    if isinstance(stat, dict):
        return int(stat["value"])
    return int(stat or 0)


async def login(client: httpx.AsyncClient, username: str, password: str) -> None:
    response = await client.post("/api/auth/login", json={"username": username, "password": password})
    response.raise_for_status()
    client.headers["Authorization"] = f"Bearer {response.json()['token']}"


async def list_websites(client: httpx.AsyncClient) -> list[dict]:
    response = await client.get("/api/websites", params={"pageSize": 100})
    response.raise_for_status()
    body = response.json()
    return body["data"] if isinstance(body, dict) else body


async def fetch_metric(client: httpx.AsyncClient, website_id: str, period: dict, metric_type: str) -> list[tuple[str, int]]:
    response = await client.get(f"/api/websites/{website_id}/metrics", params={**period, "type": metric_type})
    response.raise_for_status()
    return [(row["x"] or "(unknown)", int(row["y"])) for row in response.json()]


async def fetch_site_report(client: httpx.AsyncClient, website: dict, start: datetime, end: datetime) -> SiteReport:
    website_id = website["id"]
    period = {"startAt": int(start.timestamp() * 1000), "endAt": int(end.timestamp() * 1000)}

    response = await client.get(f"/api/websites/{website_id}/stats", params=period)
    response.raise_for_status()
    stats = response.json()

    try:
        routes = await fetch_metric(client, website_id, period, "path")
    except httpx.HTTPStatusError:
        routes = await fetch_metric(client, website_id, period, "url")  # Umami v2 calls it "url"

    return SiteReport(
        name=website["name"],
        domain=website.get("domain") or "",
        visits=read_stat(stats.get("visits")),
        visitors=read_stat(stats.get("visitors")),
        pageviews=read_stat(stats.get("pageviews")),
        countries=await fetch_metric(client, website_id, period, "country"),
        devices=await fetch_metric(client, website_id, period, "device"),
        routes=routes,
    )
