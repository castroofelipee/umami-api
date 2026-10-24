# Umami Weekly Report

FastAPI service that, once a week, pulls stats for every site in a self-hosted Umami
and posts a summary to a Discord channel via webhook: visits, countries, devices, top routes.

## Run

```bash
cp .env.example .env   # fill in Umami credentials + Discord webhook URL
uv sync
uv run uvicorn main:app --port 8000
```

Run a single worker: the scheduler lives in-process.
`/docs`, `/redoc` and `/openapi.json` exist only with `ENVIRONMENT=development`.

## Endpoints

- `POST /reports/weekly` — send the report now. Needs header `X-Trigger-Token: $TRIGGER_TOKEN`
  (disabled when `TRIGGER_TOKEN` is unset).

## Tests

```bash
uv run pytest
```
