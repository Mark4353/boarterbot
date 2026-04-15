import asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiohttp import web

from app.config import load_config
from app.db import init_db, run_migration_file
from app.handlers.start import router as start_router
from app.handlers.menus import router as menus_router
from app.handlers.registration import router as reg_router
from app.handlers.profile import router as profile_router
from app.handlers.orders import router as orders_router
from app.handlers.verify import router as verify_router
from app.handlers.moderation import router as moderation_router
from app.handlers.settings import router as settings_router
from app.webhook import create_web_app

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
        await run_migration_file(str(path))

    bot = Bot(token=cfg.bot_token, parse_mode=ParseMode.HTML)
    await bot.delete_webhook(drop_pending_updates=True)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(reg_router)
    dp.include_router(profile_router)
    dp.include_router(orders_router)
    dp.include_router(verify_router)
    dp.include_router(moderation_router)
    dp.include_router(settings_router)
    dp.include_router(menus_router)
    
    web_app = create_web_app(bot)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, cfg.webhook_host, cfg.webhook_port)
    await site.start()

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
