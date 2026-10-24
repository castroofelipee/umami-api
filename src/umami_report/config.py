from venvalid import int_, str_, venvalid

config = venvalid({
    "ENVIRONMENT": str_(allowed=["development", "production"], default="production"),
    "UMAMI_URL": str_(),
    "UMAMI_USERNAME": str_(),
    "UMAMI_PASSWORD": str_(),
    "DISCORD_WEBHOOK_URL": str_(validate=lambda url: url.startswith("https://")),
    "TRIGGER_TOKEN": str_(default=""),
    "REPORT_WEEKDAY": int_(default=0, allowed=list(range(7))),  # 0=Monday
    "REPORT_HOUR": int_(default=9, allowed=list(range(24))),
    "TIMEZONE": str_(default="America/Sao_Paulo"),
    "TOP_N": int_(default=5, validate=lambda top_n: 1 <= top_n <= 10),
})
