from __future__ import annotations

from .bot import PremioTronchiBot
from .config import load_settings
from .fantacalcio import FantacalcioClient
from .storage import Storage


def main() -> None:
    settings = load_settings()
    storage = Storage(settings.database_path)
    fantacalcio_client = FantacalcioClient(
        settings.voti_page_url,
        cookie_header=settings.fantacalcio_cookie,
    )

    bot = PremioTronchiBot(
        token=settings.telegram_bot_token,
        storage=storage,
        fantacalcio_client=fantacalcio_client,
    )
    if settings.bot_run_mode == "webhook":
        if not settings.webhook_url:
            raise ValueError("Missing WEBHOOK_URL for BOT_RUN_MODE=webhook")
        bot.run_webhook(webhook_url=settings.webhook_url, port=settings.port)
    else:
        bot.run_polling()


if __name__ == "__main__":
    main()
