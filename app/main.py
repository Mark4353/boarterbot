import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from app.config import load_config
from app.db import init_db, run_migration_file
from app.handlers.start import router as start_router
from app.handlers.menus import router as menus_router
from app.handlers.registration import router as reg_router
from app.handlers.profile import router as profile_router
from app.handlers.orders import router as orders_router
from app.handlers.verify import router as verify_router

async def main():
    cfg = load_config()

    await init_db(cfg.db_dsn)
    await run_migration_file("migrations/001_init.sql")
    await run_migration_file("migrations/002_profiles.sql")
    await run_migration_file("migrations/003_verification.sql")
    await run_migration_file("migrations/004_orders.sql")
    await run_migration_file("migrations/005_orders_editor.sql")
    await run_migration_file("migrations/006_orders_deadline.sql")

    bot = Bot(token=cfg.bot_token, parse_mode=ParseMode.HTML)
    await bot.delete_webhook(drop_pending_updates=True)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(reg_router)
    dp.include_router(profile_router)
    dp.include_router(orders_router)
    dp.include_router(verify_router)
    dp.include_router(menus_router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
