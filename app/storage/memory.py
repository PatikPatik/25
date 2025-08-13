from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone

@dataclass
class User:
    user_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class Account:
    user_id: int
    balance: int = 0

@dataclass
class Referral:
    referee_id: int
    referrer_id: int
    activated: bool = False

@dataclass
class Invoice:
    code: str
    user_id: int
    amount_nanoton: int
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    paid_at: datetime | None = None
    tx_hash: str | None = None

USERS: Dict[int, User] = {}
ACCOUNTS: Dict[int, Account] = {}
REFERRALS: Dict[int, Referral] = {}
INVOICES: Dict[str, Invoice] = {}

def upsert_user(u: User) -> None:
    USERS[u.user_id] = u
    ACCOUNTS.setdefault(u.user_id, Account(u.user_id))

def get_account(user_id: int) -> Account:
    return ACCOUNTS.setdefault(user_id, Account(user_id))

def add_balance(user_id: int, delta: int) -> int:
    acc = get_account(user_id)
    acc.balance += delta
    return acc.balance

def get_referral(referee_id: int) -> Optional[Referral]:
    return REFERRALS.get(referee_id)

def add_referral(referrer_id: int, referee_id: int) -> None:
    if referee_id not in REFERRALS and referrer_id != referee_id:
        REFERRALS[referee_id] = Referral(referee_id=referee_id, referrer_id=referrer_id)

def mark_referral_activated(referee_id: int) -> Optional[int]:
    r = REFERRALS.get(referee_id)
    if r and not r.activated:
        r.activated = True
        return r.referrer_id
    return None

def set_invoice(inv: Invoice) -> None:
    INVOICES[inv.code] = inv

def get_invoice(code: str) -> Optional[Invoice]:
    return INVOICES.get(code)
