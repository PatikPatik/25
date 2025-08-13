from __future__ import annotations
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    BOT_TOKEN: str
    ENV: str = "prod"
    MODE: str = "polling"
    BASE_URL: Optional[str] = None
    WEBHOOK_SECRET: Optional[str] = None
    SENTRY_DSN: Optional[str] = None

    TON_WALLET: str
    TON_MIN_AMOUNT: float = 0.1
    TON_INVOICE_TTL: int = 900
    TON_POLL_INTERVAL: int = 5
    TONAPI_BASE: str = "https://tonapi.io/v2"
    TONAPI_KEY: Optional[str] = None

    CREDITS_PER_TON: int = 100
    REF_BONUS_REFERRER: int = 20
    REF_BONUS_REFEREE: int = 10

    DATABASE_URL: Optional[str] = None
    ADMIN_IDS: Optional[str] = None

    @property
    def admin_ids(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]

settings = Settings()  # type: ignore[call-arg]
