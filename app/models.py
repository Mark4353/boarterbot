from dataclasses import dataclass
from typing import Optional
from app.db import pool

@dataclass
class User:
    id: int
    telegram_id: int
    username: Optional[str]
    display_name: Optional[str]
    role: str
    language: str

async def upsert_user(
    telegram_id: int,
    username: Optional[str],
    display_name: Optional[str],
    role: str,
    language: str = "ru",
) -> User:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO users (telegram_id, username, display_name, role, language)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (telegram_id)
            DO UPDATE SET username=EXCLUDED.username,
                          display_name=EXCLUDED.display_name,
                          role=EXCLUDED.role,
                          language=EXCLUDED.language
            RETURNING id, telegram_id, username, display_name, role, language
            """,
            telegram_id, username, display_name, role, language
        )
    return User(**dict(row))

async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, telegram_id, username, display_name, role, language FROM users WHERE telegram_id=$1",
            telegram_id
        )
    return User(**dict(row)) if row else None

async def get_user_by_id(user_id: int) -> Optional[User]:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, telegram_id, username, display_name, role, language FROM users WHERE id=$1",
            user_id
        )
    return User(**dict(row)) if row else None
