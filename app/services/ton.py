from __future__ import annotations
import json, re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import httpx
from ..settings import settings

NANOS = 10**9

@dataclass
class TonPaymentCheck:
    ok: bool
    tx_hash: Optional[str] = None
    from_address: Optional[str] = None
    amount_nanoton: Optional[int] = None
    raw: Optional[dict] = None

def to_nanotons(amount_ton: float) -> int:
    return int(round(amount_ton * NANOS))

def ton_deeplink(address: str, amount_ton: float, comment: str) -> str:
    from urllib.parse import quote
    return f"ton://transfer/{address}?amount={to_nanotons(amount_ton)}&text={quote(comment)}"

def _json_has_code(ev: dict, code: str) -> bool:
    ims = ev.get("in_messages") or ev.get("messages") or []
    for m in ims:
        c = (m.get("message") or m.get("comment") or "")
        if c and code in str(c):
            return True
    s = json.dumps(ev, ensure_ascii=False)
    return code in s

def _extract_amount_nanoton(ev: dict) -> int:
    ims = ev.get("in_messages") or ev.get("messages") or []
    for m in ims:
        v = m.get("value")
        if isinstance(v, str) and v.isdigit():
            return int(v)
        if isinstance(v, int):
            return v
    s = json.dumps(ev, ensure_ascii=False)
    m = re.search(r'"value"\s*:\s*"?(?P<n>\d{6,})"?', s)
    if m:
        try:
            return int(m.group("n"))
        except Exception:
            pass
    return 0

def _extract_from_address(ev: dict) -> Optional[str]:
    ims = ev.get("in_messages") or ev.get("messages") or []
    for m in ims:
        src = m.get("source") or m.get("from") or {}
        if isinstance(src, dict):
            addr = src.get("address") or src.get("account") or None
            if addr:
                return addr
        elif isinstance(src, str):
            return src
    return None

def _extract_tx_hash(ev: dict) -> Optional[str]:
    return ev.get("event_id") or ev.get("hash") or ev.get("transaction_id") or None

async def tonapi_find_payment(address: str, code: str, min_amount_nanoton: int, since: datetime) -> TonPaymentCheck:
    base = settings.TONAPI_BASE.rstrip("/")
    headers = {}
    if settings.TONAPI_KEY:
        headers["Authorization"] = f"Bearer {settings.TONAPI_KEY}"
    url = f"{base}/accounts/{address}/events?limit=50"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

    events = data.get("events", [])
    since_ts = int(since.replace(tzinfo=timezone.utc).timestamp()) - 5

    for ev in events:
        ts = ev.get("timestamp") or ev.get("utime") or ev.get("created_at") or 0
        try:
            ts = int(ts)
        except Exception:
            ts = 0
        if ts and ts < since_ts:
            continue
        if not _json_has_code(ev, code):
            continue
        amount = _extract_amount_nanoton(ev)
        if amount < min_amount_nanoton:
            continue
        return TonPaymentCheck(
            ok=True,
            tx_hash=_extract_tx_hash(ev),
            from_address=_extract_from_address(ev),
            amount_nanoton=amount,
            raw=ev,
        )
    return TonPaymentCheck(ok=False)
