from app.db import pool

async def create_order(
    client_id: int,
    title: str,
    description: str,
    budget_minor: int,
    currency: str = "USD",
) -> int:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO orders (client_id, title, description, budget_minor, currency)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            client_id,
            title,
            description,
            budget_minor,
            currency,
        )
    return int(row["id"])

async def list_orders_for_client(user_id: int, limit: int = 10) -> list[dict]:
    p = pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, title, budget_minor, currency, status, created_at
            FROM orders
            WHERE client_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )
    return [dict(r) for r in rows]

async def get_order_for_client(order_id: int, user_id: int) -> dict | None:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, title, description, budget_minor, currency, status, created_at
            FROM orders
            WHERE id = $1 AND client_id = $2
            """,
            order_id,
            user_id,
        )
    return dict(row) if row else None

async def list_open_orders(limit: int = 10) -> list[dict]:
    p = pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, title, budget_minor, currency, created_at
            FROM orders
            WHERE status = 'open'
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
    return [dict(r) for r in rows]

async def accept_order(order_id: int, editor_id: int) -> bool:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET status = 'accepted',
                editor_id = $2,
                updated_at = NOW()
            WHERE id = $1
              AND status = 'open'
              AND editor_id IS NULL
            RETURNING id
            """,
            order_id,
            editor_id,
        )
    return bool(row)
