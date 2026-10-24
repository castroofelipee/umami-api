from datetime import datetime, timedelta

import httpx

from umami_report import discord, umami
from umami_report.config import config

REPORT_PERIOD = timedelta(days=7)


async def send_weekly_report(end: datetime) -> int:
    start = end - REPORT_PERIOD
    async with httpx.AsyncClient(base_url=config["UMAMI_URL"], timeout=30) as client:
        await umami.login(client, config["UMAMI_USERNAME"], config["UMAMI_PASSWORD"])
        websites = await umami.list_websites(client)
        reports = [await umami.fetch_site_report(client, website, start, end) for website in websites]

    await discord.send_report(config["DISCORD_WEBHOOK_URL"], reports, start, end, config["TOP_N"])
    return len(reports)
