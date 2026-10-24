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
