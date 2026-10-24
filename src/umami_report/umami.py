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
