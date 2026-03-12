from aiogram import Router, F
from aiogram.types import CallbackQuery
import os

from app.models import get_user_by_telegram_id
from app.keyboards import kb_main_menu, kb_editor_menu, kb_support, kb_editor_orders_list
from app.profile_repo import get_editor_profile
from app.order_repo import list_open_orders

router = Router()

@router.callback_query(
    F.data.startswith(("client:", "editor:", "mod:", "common:", "deal:")) &
    ~F.data.in_(["client:profile", "editor:profile", "client:create_order", "client:my_orders"])
)
async def cb_menu(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer("Нажмите /start", show_alert=True)
        return

    # ✅ "В меню"
    if call.data == "common:menu":
        if user.role == "editor":
            p = await get_editor_profile(user.id)
            is_verified = bool(p and p.get("verification_status") == "verified")
            await call.message.answer("Меню:", reply_markup=kb_editor_menu(is_verified))
        else:
            await call.message.answer("Меню:", reply_markup=kb_main_menu(user.role))
        await call.answer()
        return

    # Заглушки / проверки:
    if call.data == "common:balance":
        await call.message.answer("💳 Баланс: скоро будет.")
    elif call.data == "common:support":
        admin_username = os.getenv("ADMIN_USERNAME", "").strip()
        if admin_username:
            await call.message.answer(
                "🆘 Поддержка: напишите админу.",
                reply_markup=kb_support(admin_username),
            )
        else:
            await call.message.answer("🆘 Поддержка: админ не настроен.")
    elif call.data == "mod:held_messages":
        await call.message.answer("🆕 Очередь модерации: скоро будет.")
    elif call.data == "editor:find_orders":
        p = await get_editor_profile(user.id)
        if not p or p.get("verification_status") != "verified":
            await call.answer("⛔ Сначала пройдите верификацию.", show_alert=True)
            return
        orders = await list_open_orders(limit=10)
        if not orders:
            await call.message.answer("🔎 Доступных заказов пока нет.")
        else:
            await call.message.answer(
                "🔎 Доступные заказы:",
                reply_markup=kb_editor_orders_list(orders),
            )
    elif call.data.startswith("deal:chat"):
        await call.message.answer("💬 Чат: скоро будет.")
    elif call.data.startswith("deal:change"):
        await call.message.answer("✏️ Изменить: скоро будет.")
    elif call.data.startswith("deal:dispute"):
        await call.message.answer("⚠️ Спор: скоро будет.")
    else:
        await call.message.answer(f"⏳ Раздел в разработке: {call.data}")

    # Показать меню снова
    if user.role == "editor":
        p = await get_editor_profile(user.id)
        is_verified = bool(p and p.get("verification_status") == "verified")
        await call.message.answer("Меню:", reply_markup=kb_editor_menu(is_verified))
    else:
        await call.message.answer("Меню:", reply_markup=kb_main_menu(user.role))

    await call.answer()
