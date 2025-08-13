from __future__ import annotations
import logging, secrets
from datetime import timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from ..settings import settings
from ..services.timeutils import utcnow
from ..services.ton import ton_deeplink, to_nanotons, tonapi_find_payment
from ..storage import mem as store
from ..utils.refcode import encode_ref, decode_ref

logger = logging.getLogger(__name__)

async def register_user(update: Update) -> None:
    u = update.effective_user
    store.upsert_user(store.User(
        user_id=u.id,
        username=u.username,
        first_name=u.first_name,
        last_name=u.last_name
    ))

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await register_user(update)

    # Referral handling via /start <code>
    args = context.args or []
    if args:
        code = args[0]
        referrer_id = decode_ref(code)
        if referrer_id and referrer_id != update.effective_user.id and not store.get_referral(update.effective_user.id):
            store.add_referral(referrer_id=referrer_id, referee_id=update.effective_user.id)
            logger.info("Referral linked: %s -> %s", referrer_id, update.effective_user.id)

    await update.message.reply_text(
        "Привет! Это бот с балансом и TON-оплатой.
"
        "Команды: /pay — пополнить, /balance — баланс, /ref — рефссылка, /help — помощь."
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Команды: /pay, /balance, /ref, /help")

async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await register_user(update)
    bal = store.get_account(update.effective_user.id).balance
    await update.message.reply_text(f"Ваш баланс: {bal} кредитов.")

async def cmd_ref(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await register_user(update)
    me = await context.bot.get_me()
    code = encode_ref(update.effective_user.id)
    link = f"https://t.me/{me.username}?start={code}"
    # stats
    cnt_total = sum(1 for r in store.REFERRALS.values() if r.referrer_id == update.effective_user.id)
    cnt_active = sum(1 for r in store.REFERRALS.values() if r.referrer_id == update.effective_user.id and r.activated)
    await update.message.reply_text(
        f"Ваша реферальная ссылка:
{link}

"
        f"Привлечено: {cnt_total}
Активировали оплату: {cnt_active}
"
        f"Бонусы: реферал +{settings.REF_BONUS_REFEREE}, вам +{settings.REF_BONUS_REFERRER} при первой оплате реферала."
    )

async def cmd_pay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await register_user(update)
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    amount_ton = settings.TON_MIN_AMOUNT
    code = secrets.token_hex(3).upper()
    link = ton_deeplink(settings.TON_WALLET, amount_ton, code)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("Оплатить в Tonkeeper", url=link)
    ],[
        InlineKeyboardButton("Проверить оплату", callback_data=f"check:{code}")
    ]])

    # save invoice in memory
    inv = store.Invoice(
        code=code,
        user_id=update.effective_user.id,
        amount_nanoton=to_nanotons(amount_ton),
        expires_at=utcnow() + timedelta(seconds=settings.TON_INVOICE_TTL)
    )
    store.set_invoice(inv)

    await update.message.reply_text(
        f"Счёт на {amount_ton:.3f} TON создан.
"
        f"Комментарий к переводу: {code}
"
        f"Счёт активен {settings.TON_INVOICE_TTL//60} мин.",
        reply_markup=kb
    )

async def cb_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, code = (query.data or "").split(":", 1)
    inv = store.get_invoice(code)
    if not inv:
        await query.edit_message_text("Счёт не найден или истёк.")
        return

    since = utcnow() - timedelta(seconds=settings.TON_INVOICE_TTL + 60)
    res = await tonapi_find_payment(settings.TON_WALLET, code, inv.amount_nanoton, since)
    if not res.ok:
        await query.edit_message_text("Пока не вижу поступления. Попробуй ещё раз через минуту.")
        return

    # mark paid
    inv.status = "paid"
    inv.paid_at = utcnow()
    inv.tx_hash = res.tx_hash

    # credit user balance
    credits = int(settings.CREDITS_PER_TON * (inv.amount_nanoton / 1_000_000_000))
    new_bal = store.add_balance(inv.user_id, credits)

    # activate referral bonus if first payment
    ref = store.get_referral(inv.user_id)
    if ref and not ref.activated:
        referrer_id = store.mark_referral_activated(inv.user_id)
        if referrer_id:
            store.add_balance(referrer_id, settings.REF_BONUS_REFERRER)
            store.add_balance(inv.user_id, settings.REF_BONUS_REFEREE)

    await query.edit_message_text(
        f"✅ Платёж найден! Баланс пополнен на {credits} кредитов.
"
        f"Текущий баланс: {new_bal}."
    )

def register_core_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("ref", cmd_ref))
    app.add_handler(CommandHandler("pay", cmd_pay))
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(cb_check, pattern=r"^check:"))
