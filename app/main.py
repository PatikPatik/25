from __future__ import annotations
import logging
from telegram.ext import ApplicationBuilder, AIORateLimiter
from .settings import settings
from .logging_config import setup_logging
from .handlers.core import register_core_handlers

logger = logging.getLogger(__name__)

def run() -> None:
    setup_logging()
    application = (
        ApplicationBuilder()
        .token(settings.BOT_TOKEN)
        .rate_limiter(AIORateLimiter())
        .build()
    )

    register_core_handlers(application)

    if settings.MODE.lower() != "polling":
        raise RuntimeError("Set MODE=polling for this build.")

    logger.info("Starting bot in POLLING mode")
    # run_polling will delete webhook automatically
    application.run_polling(allowed_updates=None)
