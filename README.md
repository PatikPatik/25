# Telegram Bot — Polling, TON payments, Referrals, Balance

## Environment (.env / Render)
```
MODE=polling
ENV=prod
BOT_TOKEN=<your_token>

# TON
TON_WALLET=<your_ton_address>
TON_MIN_AMOUNT=0.1
TON_INVOICE_TTL=900
TON_POLL_INTERVAL=5
TONAPI_BASE=https://tonapi.io/v2
TONAPI_KEY=

# Credits & referral
CREDITS_PER_TON=100
REF_BONUS_REFERRER=20
REF_BONUS_REFEREE=10

# Optional DB (Postgres)
DATABASE_URL=postgres://user:pass@host:5432/dbname
```

## Reset Telegram webhook once:
https://api.telegram.org/bot<YOUR_TOKEN>/deleteWebhook?drop_pending_updates=true

## Commands
- `/start` — регистрация (поддержка deeplink: `/start <code>`)
- `/pay` — создать счёт  (TON)
- `/balance` — баланс кредитов
- `/ref` — реферальная ссылка и статистика
- `/help` — помощь
- (admin) `/add_balance <user_id> <amount>`
