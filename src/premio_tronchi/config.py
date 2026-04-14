from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    voti_page_url: str
    database_path: str
    fantacalcio_cookie: str | None
    bot_run_mode: str
    webhook_url: str | None
    port: int


DEFAULT_VOTI_PAGE_URL = "https://www.fantacalcio.it/voti-fantacalcio-serie-a"


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable")

    voti_page_url = os.getenv("FANTACALCIO_VOTI_PAGE_URL", DEFAULT_VOTI_PAGE_URL).strip()
    database_path = os.getenv("DATABASE_PATH", "premio_tronchi.db").strip()
    fantacalcio_cookie = os.getenv("FANTACALCIO_COOKIE", "").strip() or None
    bot_run_mode = os.getenv("BOT_RUN_MODE", "polling").strip().lower()
    webhook_url = os.getenv("WEBHOOK_URL", "").strip() or None
    port = int(os.getenv("PORT", "10000").strip())

    if bot_run_mode not in {"polling", "webhook"}:
        raise ValueError("BOT_RUN_MODE must be either 'polling' or 'webhook'")

    return Settings(
        telegram_bot_token=token,
        voti_page_url=voti_page_url,
        database_path=database_path,
        fantacalcio_cookie=fantacalcio_cookie,
        bot_run_mode=bot_run_mode,
        webhook_url=webhook_url,
        port=port,
    )
