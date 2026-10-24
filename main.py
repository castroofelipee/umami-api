import asyncio
import contextlib
import logging
import secrets
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Header, HTTPException

from umami_report.config import config
from umami_report.report import send_weekly_report
from umami_report.scheduler import run_scheduler

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_task = asyncio.create_task(run_scheduler())
    yield
    scheduler_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await scheduler_task


is_development = config["ENVIRONMENT"] == "development"

app = FastAPI(
    title="Umami Weekly Report",
    lifespan=lifespan,
    docs_url="/docs" if is_development else None,
    redoc_url="/redoc" if is_development else None,
    openapi_url="/openapi.json" if is_development else None,
)


@app.post("/reports/weekly", include_in_schema=is_development)
async def trigger_weekly_report(x_trigger_token: str = Header(default="")) -> dict:
    expected_token = config["TRIGGER_TOKEN"]
    if not expected_token or not secrets.compare_digest(x_trigger_token, expected_token):
        raise HTTPException(status_code=403)
    sent_sites = await send_weekly_report(datetime.now(ZoneInfo(config["TIMEZONE"])))
    return {"sites": sent_sites}
