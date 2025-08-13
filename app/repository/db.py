from __future__ import annotations
import logging, os, asyncio
from typing import Optional, Any, Sequence

logger = logging.getLogger(__name__)

try:
    from psycopg_pool import AsyncConnectionPool  # type: ignore
except Exception as e:
    AsyncConnectionPool = None  # type: ignore

POOL: Optional[AsyncConnectionPool] = None

async def init_pool(dsn: Optional[str]) -> None:
    global POOL
    if not dsn or AsyncConnectionPool is None:
        logger.info("DB disabled (no DATABASE_URL or psycopg_pool missing).")
        POOL = None
        return
    POOL = AsyncConnectionPool(dsn, max_size=5, kwargs={"autocommit": True})
    async with POOL.connection() as _:
        logger.info("DB pool initialized.")

def enabled() -> bool:
    return POOL is not None

async def exec(sql: str, params: Optional[Sequence[Any]] = None) -> None:
    if not POOL:
        return
    async with POOL.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params or [])

async def fetchone(sql: str, params: Optional[Sequence[Any]] = None):
    if not POOL:
        return None
    async with POOL.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params or [])
            return await cur.fetchone()

async def fetchall(sql: str, params: Optional[Sequence[Any]] = None):
    if not POOL:
        return []
    async with POOL.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params or [])
            return await cur.fetchall()

async def ensure_schema() -> None:
    if not POOL:
        return
    await exec("""
    create table if not exists users(
        user_id bigint primary key,
        username text,
        first_name text,
        last_name text,
        created_at timestamptz default now()
    );
    create table if not exists accounts(
        user_id bigint primary key references users(user_id),
        balance integer not null default 0,
        updated_at timestamptz default now()
    );
    create table if not exists referrals(
        referee_id bigint primary key,
        referrer_id bigint not null,
        created_at timestamptz default now(),
        activated boolean not null default false,
        activated_at timestamptz
    );
    create table if not exists invoices(
        id bigserial primary key,
        code text unique not null,
        user_id bigint not null references users(user_id),
        amount_nanoton bigint not null,
        status text not null default 'pending',
        created_at timestamptz default now(),
        expires_at timestamptz not null,
        paid_at timestamptz,
        tx_hash text,
        comment text
    );
    create table if not exists transactions(
        id bigserial primary key,
        user_id bigint not null references users(user_id),
        kind text not null, -- topup|bonus_ref|spend
        amount integer not null, -- credits (+/-)
        meta jsonb,
        created_at timestamptz default now()
    );
    """)
