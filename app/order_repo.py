from app.db import pool

async def create_order(
    client_id: int,
    title: str,
    description: str,
    budget_minor: int,
    revision_price_minor: int,
    deadline_at,
    currency: str = "USD",
) -> int:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO orders (client_id, title, description, budget_minor, revision_price_minor, deadline_at, currency)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """,
            client_id,
            title,
            description,
            budget_minor,
            revision_price_minor,
            deadline_at,
            currency,
        )
    return int(row["id"])

async def list_orders_for_client(user_id: int, limit: int = 10) -> list[dict]:
    p = pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, title, budget_minor, currency, status, created_at, deadline_at
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
            SELECT id, title, description, budget_minor, revision_price_minor, currency, status, created_at, deadline_at, editor_id
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
            SELECT id, title, budget_minor, currency, created_at, deadline_at
            FROM orders
            WHERE status = 'open'
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
    return [dict(r) for r in rows]

async def list_orders_for_editor(user_id: int, limit: int = 10) -> list[dict]:
    p = pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, title, status, created_at
            FROM orders
            WHERE editor_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )
    return [dict(r) for r in rows]

async def list_deals_for_client(user_id: int, limit: int = 10) -> list[dict]:
    p = pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, title, status, created_at
            FROM orders
            WHERE client_id = $1
              AND status IN ('accepted', 'dispute')
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )
    return [dict(r) for r in rows]

async def list_deals_for_editor(user_id: int, limit: int = 10) -> list[dict]:
    p = pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, title, status, created_at
            FROM orders
            WHERE editor_id = $1
              AND status IN ('accepted', 'dispute')
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )
    return [dict(r) for r in rows]

async def get_order_by_id(order_id: int) -> dict | None:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, client_id, editor_id, title, description, budget_minor, revision_price_minor, currency, status,
                   created_at, deadline_at, dispute_opened_at, dispute_opened_by, dispute_client_agree, dispute_editor_agree,
                   agreed_price_minor, payment_status, payment_link, paid_at, stripe_session_id, revision_stripe_session_id
            FROM orders
            WHERE id = $1
            """,
            order_id,
        )
    return dict(row) if row else None

async def list_active_deals(limit: int = 20) -> list[dict]:
    p = pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, client_id, editor_id, title, status, created_at, agreed_price_minor, payment_status
            FROM orders
            WHERE status IN ('accepted', 'dispute')
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
    return [dict(r) for r in rows]

async def set_payment_status(order_id: int, payment_status: str) -> bool:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET payment_status = $2,
                updated_at = NOW()
            WHERE id = $1
            RETURNING id
            """,
            order_id,
            payment_status,
        )
    return bool(row)

async def create_deal_message(order_id: int, sender_user_id: int, sender_role: str, content: str) -> int:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO deal_messages (deal_id, sender_user_id, sender_role, content)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            order_id,
            sender_user_id,
            sender_role,
            content,
        )
    return int(row["id"])

async def get_deal_messages(order_id: int, limit: int = 50) -> list[dict]:
    p = pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT sender_user_id, sender_role, content, created_at
            FROM deal_messages
            WHERE deal_id = $1
            ORDER BY created_at ASC
            LIMIT $2
            """,
            order_id,
            limit,
        )
    return [dict(r) for r in rows]

async def open_dispute(order_id: int, opened_by: int) -> bool:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET status = 'dispute',
                dispute_opened_at = NOW(),
                dispute_opened_by = $2,
                dispute_client_agree = FALSE,
                dispute_editor_agree = FALSE,
                updated_at = NOW()
            WHERE id = $1
              AND status = 'accepted'
              AND editor_id IS NOT NULL
            RETURNING id
            """,
            order_id,
            opened_by,
        )
    return bool(row)

async def set_dispute_agree(order_id: int, user_role: str) -> tuple[bool, bool]:
    p = pool()
    async with p.acquire() as conn:
        if user_role == "client":
            row = await conn.fetchrow(
                """
                UPDATE orders
                SET dispute_client_agree = TRUE,
                    updated_at = NOW()
                WHERE id = $1 AND status = 'dispute'
                RETURNING dispute_client_agree, dispute_editor_agree
                """,
                order_id,
            )
        else:
            row = await conn.fetchrow(
                """
                UPDATE orders
                SET dispute_editor_agree = TRUE,
                    updated_at = NOW()
                WHERE id = $1 AND status = 'dispute'
                RETURNING dispute_client_agree, dispute_editor_agree
                """,
                order_id,
            )
    if not row:
        return False, False
    return bool(row["dispute_client_agree"]), bool(row["dispute_editor_agree"])

async def close_dispute(order_id: int) -> bool:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET status = 'accepted',
                updated_at = NOW()
            WHERE id = $1 AND status = 'dispute'
            RETURNING id
            """,
            order_id,
        )
    return bool(row)

async def update_order_if_open(
    order_id: int,
    client_id: int,
    title: str,
    description: str,
    budget_minor: int,
    revision_price_minor: int,
    deadline_at,
) -> bool:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET title = $3,
                description = $4,
                budget_minor = $5,
                revision_price_minor = $6,
                deadline_at = $7,
                updated_at = NOW()
            WHERE id = $1
              AND client_id = $2
              AND status = 'open'
              AND editor_id IS NULL
            RETURNING id
            """,
            order_id,
            client_id,
            title,
            description,
            budget_minor,
            revision_price_minor,
            deadline_at,
        )
    return bool(row)

async def accept_order(order_id: int, editor_id: int, agreed_price_minor: int) -> bool:
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET status = 'accepted',
                editor_id = $2,
                agreed_price_minor = $3,
                updated_at = NOW()
            WHERE id = $1
              AND status = 'open'
              AND editor_id IS NULL
            RETURNING id
            """,
            order_id,
            editor_id,
            agreed_price_minor,
        )
    return bool(row)

async def set_payment_link(order_id: int, payment_link: str, payment_session_id: str) -> bool:
    """Store payment link and LiqPay session identifier.

    Note: the database column is still named stripe_session_id for legacy compatibility.
    """
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET payment_link = $2,
                stripe_session_id = $3,
                payment_status = 'pending',
                updated_at = NOW()
            WHERE id = $1
              AND status = 'accepted'
            RETURNING id
            """,
            order_id,
            payment_link,
            payment_session_id,
        )
    return bool(row)

async def mark_order_paid(order_id: int) -> bool:
    """Mark order as paid"""
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET payment_status = 'paid',
                paid_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
            RETURNING id
            """,
            order_id,
        )
    return bool(row)

async def find_order_by_payment_session_id(session_id: str) -> tuple[dict | None, str | None]:
    """Find order by stored payment session id (main or revision)."""
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, client_id, editor_id, title, description, budget_minor, revision_price_minor, currency, status,
                   created_at, deadline_at, dispute_opened_at, dispute_opened_by, dispute_client_agree, dispute_editor_agree,
                   agreed_price_minor, payment_status, payment_link, paid_at,
                   CASE
                       WHEN stripe_session_id = $1 THEN 'order'
                       WHEN revision_stripe_session_id = $1 THEN 'revision'
                       ELSE NULL
                   END AS payment_kind
            FROM orders
            WHERE stripe_session_id = $1 OR revision_stripe_session_id = $1
            """,
            session_id,
        )
    if not row:
        return None, None
    data = dict(row)
    payment_kind = data.pop("payment_kind", None)
    return data, payment_kind

# ---------- Balance and withdrawal functions ----------

async def get_user_balance(user_id: int) -> dict:
    """Get user's virtual balance and total earned"""
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT virtual_balance_minor, total_earned_minor, verified_for_withdrawal
            FROM users
            WHERE id = $1
            """,
            user_id,
        )
    return dict(row) if row else {"virtual_balance_minor": 0, "total_earned_minor": 0, "verified_for_withdrawal": False}

async def add_to_balance(user_id: int, amount_minor: int, transaction_type: str, order_id: int | None = None, description: str = "") -> bool:
    """Add amount to user's virtual balance and log transaction"""
    p = pool()
    async with p.acquire() as conn:
        async with conn.transaction():
            # Update balance
            row = await conn.fetchrow(
                """
                UPDATE users
                SET virtual_balance_minor = virtual_balance_minor + $2,
                    total_earned_minor = total_earned_minor + $2,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING id
                """,
                user_id,
                amount_minor,
            )
            if not row:
                return False

            # Log transaction
            await conn.execute(
                """
                INSERT INTO balance_transactions (user_id, amount_minor, transaction_type, order_id, description)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id,
                amount_minor,
                transaction_type,
                order_id,
                description,
            )
    return True

async def withdraw_balance(user_id: int, amount_minor: int, description: str = "") -> bool:
    """Withdraw from user's virtual balance"""
    p = pool()
    async with p.acquire() as conn:
        async with conn.transaction():
            # Check balance
            row = await conn.fetchrow(
                """
                SELECT virtual_balance_minor, verified_for_withdrawal
                FROM users
                WHERE id = $1
                """,
                user_id,
            )
            if not row or row["virtual_balance_minor"] < amount_minor or not row["verified_for_withdrawal"]:
                return False

            # Update balance
            row = await conn.fetchrow(
                """
                UPDATE users
                SET virtual_balance_minor = virtual_balance_minor - $2,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING id
                """,
                user_id,
                amount_minor,
            )
            if not row:
                return False

            # Log transaction
            await conn.execute(
                """
                INSERT INTO balance_transactions (user_id, amount_minor, transaction_type, description)
                VALUES ($1, $2, 'withdrawn', $3)
                """,
                user_id,
                -amount_minor,
                description,
            )
    return True

async def list_balance_transactions(user_id: int, limit: int = 20) -> list[dict]:
    """Get user's balance transaction history"""
    p = pool()
    async with p.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT amount_minor, transaction_type, order_id, description, created_at
            FROM balance_transactions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )
    return [dict(r) for r in rows]

async def set_user_withdrawal_verification(user_id: int, verified: bool) -> bool:
    """Set user's withdrawal verification status"""
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE users
            SET verified_for_withdrawal = $2,
                updated_at = NOW()
            WHERE id = $1
            RETURNING id
            """,
            user_id,
            verified,
        )
    return bool(row)

# ---------- Revision functions ----------

async def request_revision(order_id: int, revision_description: str, proposed_price_minor: int) -> bool:
    """Client requests revision with proposed price"""
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET revision_requested = TRUE,
                revision_description = $2,
                revision_price_minor = $3,
                revision_status = 'requested',
                updated_at = NOW()
            WHERE id = $1 AND status = 'accepted'
            RETURNING id
            """,
            order_id,
            revision_description,
            proposed_price_minor,
        )
    return bool(row)

async def respond_to_revision(order_id: int, accepted: bool, counter_price_minor: int | None = None) -> bool:
    """Editor responds to revision request"""
    p = pool()
    async with p.acquire() as conn:
        if accepted:
            revision_price = counter_price_minor if counter_price_minor is not None else None
            row = await conn.fetchrow(
                """
                UPDATE orders
                SET revision_status = 'accepted',
                    revision_price_minor = COALESCE($2, revision_price_minor),
                    updated_at = NOW()
                WHERE id = $1 AND revision_status = 'requested'
                RETURNING id
                """,
                order_id,
                revision_price,
            )
        else:
            row = await conn.fetchrow(
                """
                UPDATE orders
                SET revision_status = 'rejected',
                    updated_at = NOW()
                WHERE id = $1 AND revision_status = 'requested'
                RETURNING id
                """,
                order_id,
            )
    return bool(row)

async def set_revision_payment_link(order_id: int, payment_link: str, payment_session_id: str) -> bool:
    """Set payment link for revision"""
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET revision_payment_link = $2,
                revision_stripe_session_id = $3,
                revision_status = 'payment_pending',
                updated_at = NOW()
            WHERE id = $1 AND revision_status = 'accepted'
            RETURNING id
            """,
            order_id,
            payment_link,
            payment_session_id,
        )
    return bool(row)

async def mark_revision_paid(order_id: int) -> bool:
    """Mark revision as paid"""
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET revision_status = 'paid',
                updated_at = NOW()
            WHERE id = $1
            RETURNING id
            """,
            order_id,
        )
    return bool(row)

# ---------- Order completion functions ----------

async def mark_final_video_sent(order_id: int) -> bool:
    """Editor marks that final video has been sent"""
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET final_video_sent = TRUE,
                updated_at = NOW()
            WHERE id = $1 AND status = 'accepted'
            RETURNING id
            """,
            order_id,
        )
    return bool(row)

async def confirm_order_completion(order_id: int) -> bool:
    """Client confirms order completion"""
    p = pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE orders
            SET client_confirmed_completion = TRUE,
                status = 'completed',
                updated_at = NOW()
            WHERE id = $1 AND status = 'accepted' AND final_video_sent = TRUE
            RETURNING id
            """,
            order_id,
        )
    return bool(row)

async def complete_order_and_credit_editor(order_id: int) -> bool:
    """Complete order, credit editor's balance, and delete order if no disputes"""
    p = pool()
    async with p.acquire() as conn:
        async with conn.transaction():
            # Get order details
            order = await conn.fetchrow(
                """
                SELECT editor_id, agreed_price_minor, revision_price_minor, revision_status
                FROM orders
                WHERE id = $1 AND status = 'completed' AND client_confirmed_completion = TRUE
                """,
                order_id,
            )
            if not order:
                return False

            editor_id = order["editor_id"]
            base_amount = order["agreed_price_minor"] or 0
            revision_amount = order["revision_price_minor"] or 0 if order["revision_status"] == "paid" else 0
            total_amount = base_amount + revision_amount

            # Credit editor's balance
            await conn.execute(
                """
                UPDATE users
                SET virtual_balance_minor = virtual_balance_minor + $2,
                    total_earned_minor = total_earned_minor + $2,
                    updated_at = NOW()
                WHERE id = $1
                """,
                editor_id,
                total_amount,
            )

            # Log transaction
            await conn.execute(
                """
                INSERT INTO balance_transactions (user_id, amount_minor, transaction_type, order_id, description)
                VALUES ($1, $2, 'earned', $3, 'Order completion')
                """,
                editor_id,
                total_amount,
                order_id,
                f"Order #{order_id} completed",
            )

            # Delete the completed order (no disputes)
            await conn.execute(
                "DELETE FROM orders WHERE id = $1",
                order_id,
            )

    return True
