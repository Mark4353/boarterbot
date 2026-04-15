from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    bot_token: str
    db_dsn: str
    redis_dsn: str
    moderator_ids: set[int]
    default_language: str
    liqpay_public_key: str
    liqpay_private_key: str
    liqpay_sandbox: bool
    app_url: str
    webhook_host: str
    webhook_port: int

def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is missing")

    db_dsn = os.getenv("DB_DSN", "").strip()
    redis_dsn = os.getenv("REDIS_DSN", "").strip()
    default_language = os.getenv("DEFAULT_LANGUAGE", "en").strip()
    liqpay_public_key = os.getenv("LIQPAY_PUBLIC_KEY", "").strip()
    liqpay_private_key = os.getenv("LIQPAY_PRIVATE_KEY", "").strip()
    liqpay_sandbox = os.getenv("LIQPAY_SANDBOX", "0").strip() in {"1", "true", "True", "yes", "on"}
    app_url = os.getenv("APP_URL", "https://example.com").strip()
    webhook_host = os.getenv("WEBHOOK_HOST", "0.0.0.0").strip()
    try:
        webhook_port = int(os.getenv("WEBHOOK_PORT", "8080").strip())
    except ValueError:
        webhook_port = 8080

    raw_mods = os.getenv("MODERATOR_IDS", "").strip()
    moderator_ids: set[int] = set()
    if raw_mods:
        for x in raw_mods.split(","):
            x = x.strip()
            if x.isdigit():
                moderator_ids.add(int(x))

    return Config(
        bot_token=token,
        db_dsn=db_dsn,
        redis_dsn=redis_dsn,
        moderator_ids=moderator_ids,
        default_language=default_language,
        liqpay_public_key=liqpay_public_key,
        liqpay_private_key=liqpay_private_key,
        liqpay_sandbox=liqpay_sandbox,
        app_url=app_url,
        webhook_host=webhook_host,
        webhook_port=webhook_port,
    )
