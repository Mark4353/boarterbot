import asyncio
from pathlib import Path

from app.config import load_config
from app.db import init_db, run_migration_file

async def main():
    cfg = load_config()
    await init_db(cfg.db_dsn)
    base_dir = Path(__file__).resolve().parent.parent
    migrations_dir = base_dir / "migrations"
    migration_files = [
        "001_init.sql",
        "002_profiles.sql",
        "003_verification.sql",
        "004_orders.sql",
        "005_orders_editor.sql",
        "006_orders_deadline.sql",
        "007_orders_revision_price.sql",
        "008_orders_dispute.sql",
        "009_moderation.sql",
        "010_payment.sql",
        "011_editor_profile_extended.sql",
        "012_orders_agreed_price.sql",
        "013_deal_messages.sql",
        "014_balance_and_revisions.sql",
    ]
    for name in migration_files:
        path = migrations_dir / name
        print(f"Applying {path}")
        await run_migration_file(str(path))

if __name__ == "__main__":
    asyncio.run(main())
