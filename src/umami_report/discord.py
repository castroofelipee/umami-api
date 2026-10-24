import asyncio
from collections import Counter
from datetime import datetime

import httpx

from umami_report.umami import SiteReport

EMBED_COLOR = 0x5865F2
MAX_SITE_NAME_LENGTH = 16
MAX_ROUTE_LENGTH = 20
MAX_RATE_LIMIT_RETRIES = 5


def render_table(
    headers: list[str], rows: list[list[str]], total_row: list[str] | None = None, left_columns: int = 1
) -> str:
    """Box-drawn table inside a code block; the first `left_columns` (text) are left-aligned, numbers right-aligned."""
    if not rows:
        return "```\nNo data this week\n```"

    all_rows = [headers, *rows, *([total_row] if total_row else [])]
    widths = [max(len(cell) for cell in column) for column in zip(*all_rows)]

    def render_row(cells: list[str]) -> str:
        aligned = [cell.ljust(width) if index < left_columns else cell.rjust(width) for index, (cell, width) in enumerate(zip(cells, widths))]
        return "│ " + " │ ".join(aligned) + " │"

    def render_border(left: str, middle: str, right: str) -> str:
        return left + middle.join("─" * (width + 2) for width in widths) + right

    lines = [
        render_border("┌", "┬", "┐"),
        render_row(headers),
        render_border("├", "┼", "┤"),
        *(render_row(row) for row in rows),
    ]
    if total_row:
        lines += [render_border("├", "┼", "┤"), render_row(total_row)]
    lines.append(render_border("└", "┴", "┘"))
    return "```\n" + "\n".join(lines) + "\n```"


def format_share(count: int, total: int) -> str:
    if total == 0:
        return "-"
    return f"{count / total:.1%}"


def shorten(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def sum_across_sites(entries_per_site: list[list[tuple[str, int]]], top_n: int) -> list[tuple[str, int]]:
    totals: Counter[str] = Counter()
    for entries in entries_per_site:
        for name, count in entries:
            totals[name] += count
    return totals.most_common(top_n)


def build_overview_table(reports: list[SiteReport]) -> str:
    rows = [
        [shorten(report.name, MAX_SITE_NAME_LENGTH), f"{report.visits:,}", f"{report.visitors:,}", f"{report.pageviews:,}"]
        for report in sorted(reports, key=lambda report: report.visits, reverse=True)
    ]
    total_row = [
        "Total",
        f"{sum(report.visits for report in reports):,}",
        f"{sum(report.visitors for report in reports):,}",
        f"{sum(report.pageviews for report in reports):,}",
    ]
    return render_table(["Site", "Visits", "Visitors", "Views"], rows, total_row)


def build_ranking_table(label: str, entries: list[tuple[str, int]], total: int) -> str:
    rows = [[name, f"{count:,}", format_share(count, total)] for name, count in entries]
    return render_table([label, "Visitors", "Share"], rows)


def build_top_routes_table(reports: list[SiteReport], top_n: int) -> str:
    # Routes are not summed across sites: "/" on one site is a different page from "/" on another.
    site_routes = [(report.name, route, count) for report in reports for route, count in report.routes]
    top_routes = sorted(site_routes, key=lambda site_route: site_route[2], reverse=True)[:top_n]
    rows = [
        [shorten(site_name, MAX_SITE_NAME_LENGTH), shorten(route, MAX_ROUTE_LENGTH), f"{count:,}"]
        for site_name, route, count in top_routes
    ]
    return render_table(["Site", "Route", "Views"], rows, left_columns=2)


def build_report_embed(reports: list[SiteReport], start: datetime, end: datetime, top_n: int) -> dict:
    total_visitors = sum(report.visitors for report in reports)
    countries = sum_across_sites([report.countries for report in reports], top_n)
    devices = sum_across_sites([[(device.capitalize(), count) for device, count in report.devices] for report in reports], top_n)

    return {
        "title": "📊 Weekly analytics",
        # Overview goes in the description (4096 chars) rather than a field (1024) so it fits many sites.
        # shortcut: past ~40 sites the overview outgrows the 6000-char embed limit, split it then.
        "description": f"{start:%b %d} – {end:%b %d, %Y} · {len(reports)} site(s)\n{build_overview_table(reports)}",
        "color": EMBED_COLOR,
        "fields": [
            {"name": "🌍 Where from", "value": build_ranking_table("Country", countries, total_visitors)},
            {"name": "💻 Devices", "value": build_ranking_table("Device", devices, total_visitors)},
            {"name": "🔥 Top routes", "value": build_top_routes_table(reports, top_n)},
        ],
        "footer": {"text": "Umami Analytics"},
        "timestamp": end.isoformat(),
    }


async def post_message(client: httpx.AsyncClient, webhook_url: str, payload: dict) -> None:
    for _ in range(MAX_RATE_LIMIT_RETRIES):
        response = await client.post(webhook_url, json=payload)
        if response.status_code != 429:
            response.raise_for_status()
            return
        await asyncio.sleep(float(response.json().get("retry_after", 1)))
    response.raise_for_status()


async def send_report(webhook_url: str, reports: list[SiteReport], start: datetime, end: datetime, top_n: int) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        await post_message(client, webhook_url, {"embeds": [build_report_embed(reports, start, end, top_n)]})
