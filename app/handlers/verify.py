import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.models import get_user_by_telegram_id
from app.states import Verify
from app.profile_repo import get_editor_profile, set_editor_test_submission, set_editor_verification
from app.keyboards import kb_nav_menu_help, kb_editor_menu

router = Router()

def _moderator_ids() -> list[int]:
    raw = os.getenv("MODERATOR_IDS", "").strip()
    if not raw:
        return []
    ids: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids

@router.callback_query(F.data == "verify:start")
async def verify_start(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer("Нажмите /start", show_alert=True)
        return
    if user.role != "editor":
        await call.answer("Верификация доступна только монтажёрам.", show_alert=True)
        return

    p = await get_editor_profile(user.id)
    status = (p.get("verification_status") if p else None) or "not_submitted"
    if status == "verified":
        await call.message.answer("Вы уже верифицированы.", reply_markup=kb_editor_menu(True))
        await call.answer()
        return
    if status == "pending":
        await call.message.answer("Заявка уже отправлена. Ожидайте ответа.")
        await call.answer()
        return

    await state.clear()
    await state.set_state(Verify.waiting_submission)
    await call.answer()
    await call.message.answer(
        "Выберите удобные дату и время для проверки.\nПример: 2026-03-15 18:30",
        reply_markup=kb_nav_menu_help(back="common:menu"),
    )

@router.message(Verify.waiting_submission)
async def verify_submit(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    if user.role != "editor":
        await state.clear()
        await message.answer("Верификация доступна только монтажёрам.")
        return

    submission = (message.text or "").strip()
    if not submission:
        await message.answer("Введите дату и время. Пример: 2026-03-15 18:30")
        return

    await set_editor_test_submission(user.id, submission)
    await state.clear()

    mods = _moderator_ids()
    text = "Новая заявка на верификацию\n"
    if message.from_user.username:
        text += f"Юз: @{message.from_user.username}\n"
    else:
        text += f"User ID: {message.from_user.id}\n"
    text += f"Время: {submission}"

    if mods:
        for mod_id in mods:
            try:
                await message.bot.send_message(mod_id, text)
            except:
                pass
        await message.answer("Заявка отправлена модераторам.", reply_markup=kb_editor_menu(False))
    else:
        await message.answer("Модераторы не настроены. Обратитесь в поддержку.", reply_markup=kb_editor_menu(False))

@router.callback_query(F.data == "verify:auto")
async def verify_auto(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer("Нажмите /start", show_alert=True)
        return
    if user.role != "editor":
        await call.answer("Доступно только монтажёрам.", show_alert=True)
        return

    await set_editor_verification(user.id, "verified", note="auto")
    await call.message.answer("✅ Верификация пройдена (тест).", reply_markup=kb_editor_menu(True))
    await call.answer()
