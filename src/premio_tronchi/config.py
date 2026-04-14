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


DEFAULT_VOTI_PAGE_URL = "https://www.fantacalcio.it/voti-fantacalcio-serie-a"


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable")

    voti_page_url = os.getenv("FANTACALCIO_VOTI_PAGE_URL", DEFAULT_VOTI_PAGE_URL).strip()
    database_path = os.getenv("DATABASE_PATH", "premio_tronchi.db").strip()
    fantacalcio_cookie = os.getenv("FANTACALCIO_COOKIE", "").strip() or None

    return Settings(
        telegram_bot_token=token,
        voti_page_url=voti_page_url,
        database_path=database_path,
        fantacalcio_cookie=fantacalcio_cookie,
    )
