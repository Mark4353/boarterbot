from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.models import get_user_by_telegram_id, upsert_user
from app.profile_repo import get_editor_profile, get_client_profile
from app.keyboards import (
    kb_profile,
    kb_change_role_confirm,
    kb_main_menu,
    kb_editor_menu,
)

router = Router()


def money_from_minor(minor: int, currency: str) -> str:
    return f"{minor / 100:.2f} {currency}"


@router.callback_query(F.data.in_({"editor:profile", "client:profile"}))
async def show_profile(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer("Нажмите /start", show_alert=True)
        return

    if user.role == "editor":
        p = await get_editor_profile(user.id)

        if not p:
            text = (
                "👤 Профиль монтажёра\n\n"
                "Анкета ещё не заполнена.\n"
                "Нажмите «Изменить информацию»."
            )
            status = "not_submitted"
        else:
            status = p.get("verification_status") or "not_submitted"
            status_label = {
                "not_submitted": "❌ Не пройдена",
                "pending": "🕒 На проверке",
                "verified": "✅ Верифицирован",
                "rejected": "⛔ Отклонено",
            }.get(status, status)

            price = money_from_minor(int(p.get("price_from_minor") or 0), "USD")
            portfolio = p.get("portfolio_url") or "—"

            text = (
                "👤 Профиль монтажёра\n\n"
                f"Имя: {p.get('name') or '—'}\n"
                f"Специализации: {p.get('skills') or '—'}\n"
                f"Цена от: {price}\n"
                f"Портфолио: {portfolio}\n\n"
                f"Верификация: {status_label}\n"
                f"\nРоль: монтажёр"
            )

            if status == "rejected" and p.get("verification_note"):
                text += f"\nПричина: {p['verification_note']}"

        markup = kb_profile("editor", status)

    elif user.role == "client":
        p = await get_client_profile(user.id)
        name = (p.get("name") if p else None) or "—"

        text = (
            "👤 Профиль заказчика\n\n"
            f"Имя: {name}\n\n"
            "Роль: заказчик"
        )
        markup = kb_profile("client", None)

    else:
        text = "👤 Профиль модератора"
        markup = kb_profile("moderator", None)

    try:
        await call.message.edit_text(text, reply_markup=markup)
    except:
        await call.message.answer(text, reply_markup=markup)

    await call.answer()


@router.callback_query(F.data == "profile:change_role")
async def change_role_menu(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer("Нажмите /start", show_alert=True)
        return

    text = (
        "🔁 Смена роли\n\n"
        "Выберите роль. Профили сохранятся."
    )

    try:
        await call.message.edit_text(text, reply_markup=kb_change_role_confirm())
    except:
        await call.message.answer(text, reply_markup=kb_change_role_confirm())

    await call.answer()


@router.callback_query(F.data == "profile:back")
async def profile_back(call: CallbackQuery):
    await show_profile(call)


@router.callback_query(F.data.startswith("profile:set_role:"))
async def profile_set_role(call: CallbackQuery):
    new_role = call.data.split(":")[-1]  # client/editor

    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer("Нажмите /start", show_alert=True)
        return

    tg = call.from_user
    display_name = (tg.full_name or "").strip() or tg.username or "User"

    await upsert_user(
        telegram_id=tg.id,
        username=tg.username,
        display_name=display_name,
        role=new_role,
        language=user.language,
    )

    if new_role == "editor":
        p = await get_editor_profile(user.id)
        is_verified = bool(p and p.get("verification_status") == "verified")
        markup = kb_editor_menu(is_verified)
    else:
        markup = kb_main_menu(new_role)

    try:
        await call.message.edit_text("✅ Роль изменена.", reply_markup=markup)
    except:
        await call.message.answer("✅ Роль изменена.", reply_markup=markup)

    await call.answer()