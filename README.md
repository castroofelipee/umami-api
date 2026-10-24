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

## Deploy (Docker / Coolify)

```bash
docker compose up -d --build
```

Set `UMAMI_URL`, `UMAMI_USERNAME`, `UMAMI_PASSWORD` and `DISCORD_WEBHOOK_URL` (plus optional
`TRIGGER_TOKEN`) as environment variables. In Coolify, pick the Docker Compose build pack for
this repository and fill them in under Environment Variables. Keep a single replica.

## Endpoints

- `POST /reports/weekly` — send the report now. Needs header `X-Trigger-Token: $TRIGGER_TOKEN`
  (disabled when `TRIGGER_TOKEN` is unset).

## Tests

```bash
uv run pytest
```

## License

[AGPL-3.0-or-later](LICENSE)
