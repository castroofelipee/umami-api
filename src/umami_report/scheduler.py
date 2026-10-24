import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from umami_report.config import config
from umami_report.report import send_weekly_report

logger = logging.getLogger(__name__)

MAX_SLEEP_SECONDS = 60


def next_run(after: datetime, weekday: int, hour: int) -> datetime:
    """First moment strictly after `after` that falls on `weekday` at `hour`:00."""
    days_ahead = (weekday - after.weekday()) % 7
    candidate = after.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
    if candidate <= after:
        candidate += timedelta(days=7)
    return candidate


async def sleep_until(moment: datetime) -> None:
    # asyncio.sleep runs on the monotonic clock, which drifts from wall time and can pause while
    # the host is suspended, so a single week-long sleep may wake early or late. Re-check often.
    while (remaining := (moment - datetime.now(moment.tzinfo)).total_seconds()) > 0:
        await asyncio.sleep(min(remaining, MAX_SLEEP_SECONDS))


async def run_scheduler() -> None:
    timezone = ZoneInfo(config["TIMEZONE"])
    run_at = next_run(datetime.now(timezone), config["REPORT_WEEKDAY"], config["REPORT_HOUR"])
    while True:
        logger.info("Next weekly report scheduled for %s", run_at)
        await sleep_until(run_at)
        try:
            # Report period ends at the scheduled time, not at wake-up time, so weeks never overlap or gap.
            await send_weekly_report(run_at)
        except Exception:
            logger.exception("Weekly report for %s failed", run_at)
        # Advance from the scheduled time, never from "now": guarantees exactly one send per slot.
        run_at = next_run(run_at, config["REPORT_WEEKDAY"], config["REPORT_HOUR"])
