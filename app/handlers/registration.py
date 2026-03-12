from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.models import get_user_by_telegram_id, upsert_user
from app.keyboards import (
    kb_nav,
    kb_main_menu,
    kb_editor_menu,
    kb_edit_editor_menu,
    kb_edit_client_menu,
)
from app.states import RegClient, RegEditor, EditEditor, EditClient
from app.profile_repo import (
    upsert_client_profile,
    upsert_editor_profile,
    get_editor_profile,
    get_client_profile,
)

router = Router()

# ---------- helpers for clean chat ----------

async def safe_delete_message(message: Message | None):
    if not message:
        return
    try:
        await message.delete()
    except:
        pass

async def safe_delete_by_id(bot, chat_id: int, message_id: int | None):
    if not message_id:
        return
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

async def set_last_bot_message(state: FSMContext, message_id: int):
    await state.update_data(last_bot_message_id=message_id)

async def clear_last_bot_message(state: FSMContext, bot, chat_id: int):
    data = await state.get_data()
    await safe_delete_by_id(bot, chat_id, data.get("last_bot_message_id"))
    await state.update_data(last_bot_message_id=None)

async def send_clean(message: Message, state: FSMContext, text: str, reply_markup=None):
    await clear_last_bot_message(state, message.bot, message.chat.id)
    msg = await message.answer(text, reply_markup=reply_markup)
    await set_last_bot_message(state, msg.message_id)
    return msg

async def send_clean_from_call(call: CallbackQuery, state: FSMContext, text: str, reply_markup=None):
    chat_id = call.message.chat.id
    await clear_last_bot_message(state, call.bot, chat_id)
    try:
        await safe_delete_message(call.message)
    except:
        pass
    msg = await call.message.answer(text, reply_markup=reply_markup)
    await set_last_bot_message(state, msg.message_id)
    return msg

# ---------- start role registration ----------

@router.callback_query(F.data.startswith("role:"))
async def cb_role(call: CallbackQuery, state: FSMContext):
    role = call.data.split(":", 1)[1]
    tg = call.from_user
    display_name = (tg.full_name or "").strip() or tg.username or "User"

    await upsert_user(
        telegram_id=tg.id,
        username=tg.username,
        display_name=display_name,
        role=role,
        language="ru",
    )

    await call.answer()

    if role == "editor":
        await state.clear()
        await state.set_state(RegEditor.waiting_name)
        await send_clean_from_call(
            call,
            state,
            "Введите имя (как показывать заказчикам):",
            reply_markup=kb_nav(cancel="reg:cancel")
        )
    else:
        await state.clear()
        await state.set_state(RegClient.waiting_name)
        await send_clean_from_call(
            call,
            state,
            "Введите имя (как показывать исполнителям):",
            reply_markup=kb_nav(cancel="reg:cancel")
        )

# ---------- initial client registration ----------

@router.message(RegClient.waiting_name)
async def save_client_name(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return

    name = (message.text or "").strip()
    await upsert_client_profile(user_id=user.id, name=name)
    await safe_delete_message(message)
    await state.clear()
    await clear_last_bot_message(state, message.bot, message.chat.id)
    await message.answer("✅ Профиль заказчика обновлён!", reply_markup=kb_main_menu("client"))

# ---------- initial editor registration ----------

@router.message(RegEditor.waiting_name)
async def editor_step_name(message: Message, state: FSMContext):
    await state.update_data(name=(message.text or "").strip())
    await safe_delete_message(message)
    await state.set_state(RegEditor.waiting_skills)
    await send_clean(
        message,
        state,
        "Специализации через запятую (Shorts, YouTube, Reels):",
        reply_markup=kb_nav(cancel="reg:cancel")
    )

@router.message(RegEditor.waiting_skills)
async def editor_step_skills(message: Message, state: FSMContext):
    await state.update_data(skills=(message.text or "").strip())
    await safe_delete_message(message)
    await state.set_state(RegEditor.waiting_price)
    await send_clean(
        message,
        state,
        "Минимальная цена (число). Например: 20",
        reply_markup=kb_nav(cancel="reg:cancel")
    )

@router.message(RegEditor.waiting_price)
async def editor_step_price(message: Message, state: FSMContext):
    raw = (message.text or "").strip()
    await safe_delete_message(message)

    if not raw.isdigit():
        await send_clean(
            message,
            state,
            "Цена должна быть числом. Например: 20",
            reply_markup=kb_nav(cancel="reg:cancel")
        )
        return

    await state.update_data(price_from_minor=int(raw) * 100)
    await state.set_state(RegEditor.waiting_portfolio)
    await send_clean(
        message,
        state,
        "Ссылка на портфолио:",
        reply_markup=kb_nav(cancel="reg:cancel")
    )

@router.message(RegEditor.waiting_portfolio)
async def editor_step_portfolio(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return

    data = await state.get_data()
    await upsert_editor_profile(
        user_id=user.id,
        name=data.get("name", ""),
        skills=data.get("skills", ""),
        price_from_minor=int(data.get("price_from_minor") or 0),
        portfolio_url=(message.text or "").strip(),
    )

    await safe_delete_message(message)
    await state.clear()
    await clear_last_bot_message(state, message.bot, message.chat.id)

    p = await get_editor_profile(user.id)
    is_verified = bool(p and p.get("verification_status") == "verified")

    await message.answer(
        "✅ Профиль монтажёра обновлён!",
        reply_markup=kb_editor_menu(is_verified)
    )

# ---------- edit menus ----------

@router.callback_query(F.data == "edit:editor_menu")
async def edit_editor_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await send_clean_from_call(
        call,
        state,
        "Что хотите изменить?",
        reply_markup=kb_edit_editor_menu()
    )

@router.callback_query(F.data == "edit:client_menu")
async def edit_client_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await send_clean_from_call(
        call,
        state,
        "Что хотите изменить?",
        reply_markup=kb_edit_client_menu()
    )

# ---------- edit client fields ----------

@router.callback_query(F.data == "edit:client:name")
async def edit_client_name_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditClient.waiting_name)
    await call.answer()
    await send_clean_from_call(
        call,
        state,
        "Введите новое имя:",
        reply_markup=kb_nav(cancel="edit:client_menu")
    )

@router.message(EditClient.waiting_name)
async def edit_client_name_save(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return

    name = (message.text or "").strip()
    await upsert_client_profile(user_id=user.id, name=name)
    await safe_delete_message(message)
    await state.clear()

    await send_clean(
        message,
        state,
        "✅ Имя обновлено.\n\nЧто хотите изменить дальше?",
        reply_markup=kb_edit_client_menu()
    )

# ---------- edit editor fields ----------

@router.callback_query(F.data == "edit:editor:name")
async def edit_editor_name_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditEditor.waiting_name)
    await call.answer()
    await send_clean_from_call(
        call,
        state,
        "Введите новое имя:",
        reply_markup=kb_nav(cancel="edit:editor_menu")
    )

@router.message(EditEditor.waiting_name)
async def edit_editor_name_save(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    p = await get_editor_profile(user.id)
    if not user or not p:
        return

    await upsert_editor_profile(
        user_id=user.id,
        name=(message.text or "").strip(),
        skills=p.get("skills") or "",
        price_from_minor=int(p.get("price_from_minor") or 0),
        portfolio_url=p.get("portfolio_url") or "",
    )

    await safe_delete_message(message)
    await state.clear()
    await send_clean(
        message,
        state,
        "✅ Имя обновлено.\n\nЧто хотите изменить дальше?",
        reply_markup=kb_edit_editor_menu()
    )

@router.callback_query(F.data == "edit:editor:skills")
async def edit_editor_skills_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditEditor.waiting_skills)
    await call.answer()
    await send_clean_from_call(
        call,
        state,
        "Введите новые специализации через запятую:",
        reply_markup=kb_nav(cancel="edit:editor_menu")
    )

@router.message(EditEditor.waiting_skills)
async def edit_editor_skills_save(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    p = await get_editor_profile(user.id)
    if not user or not p:
        return

    await upsert_editor_profile(
        user_id=user.id,
        name=p.get("name") or "",
        skills=(message.text or "").strip(),
        price_from_minor=int(p.get("price_from_minor") or 0),
        portfolio_url=p.get("portfolio_url") or "",
    )

    await safe_delete_message(message)
    await state.clear()
    await send_clean(
        message,
        state,
        "✅ Специализации обновлены.\n\nЧто хотите изменить дальше?",
        reply_markup=kb_edit_editor_menu()
    )

@router.callback_query(F.data == "edit:editor:price")
async def edit_editor_price_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditEditor.waiting_price)
    await call.answer()
    await send_clean_from_call(
        call,
        state,
        "Введите новую цену (число):",
        reply_markup=kb_nav(cancel="edit:editor_menu")
    )

@router.message(EditEditor.waiting_price)
async def edit_editor_price_save(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    p = await get_editor_profile(user.id)
    if not user or not p:
        return

    raw = (message.text or "").strip()
    await safe_delete_message(message)

    if not raw.isdigit():
        await send_clean(
            message,
            state,
            "Цена должна быть числом. Например: 20",
            reply_markup=kb_nav(cancel="edit:editor_menu")
        )
        return

    await upsert_editor_profile(
        user_id=user.id,
        name=p.get("name") or "",
        skills=p.get("skills") or "",
        price_from_minor=int(raw) * 100,
        portfolio_url=p.get("portfolio_url") or "",
    )

    await state.clear()
    await send_clean(
        message,
        state,
        "✅ Цена обновлена.\n\nЧто хотите изменить дальше?",
        reply_markup=kb_edit_editor_menu()
    )

@router.callback_query(F.data == "edit:editor:portfolio")
async def edit_editor_portfolio_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditEditor.waiting_portfolio)
    await call.answer()
    await send_clean_from_call(
        call,
        state,
        "Введите новую ссылку на портфолио:",
        reply_markup=kb_nav(cancel="edit:editor_menu")
    )

@router.message(EditEditor.waiting_portfolio)
async def edit_editor_portfolio_save(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    p = await get_editor_profile(user.id)
    if not user or not p:
        return

    await upsert_editor_profile(
        user_id=user.id,
        name=p.get("name") or "",
        skills=p.get("skills") or "",
        price_from_minor=int(p.get("price_from_minor") or 0),
        portfolio_url=(message.text or "").strip(),
    )

    await safe_delete_message(message)
    await state.clear()
    await send_clean(
        message,
        state,
        "✅ Портфолио обновлено.\n\nЧто хотите изменить дальше?",
        reply_markup=kb_edit_editor_menu()
    )

# ---------- cancel ----------

@router.callback_query(F.data == "reg:cancel")
async def reg_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()

    user = await get_user_by_telegram_id(call.from_user.id)
    await clear_last_bot_message(state, call.bot, call.message.chat.id)

    if user:
        if user.role == "editor":
            p = await get_editor_profile(user.id)
            is_verified = bool(p and p.get("verification_status") == "verified")
            await call.message.answer("Ок, отменено.", reply_markup=kb_editor_menu(is_verified))
        else:
            await call.message.answer("Ок, отменено.", reply_markup=kb_main_menu(user.role))
    else:
        await call.message.answer("Ок, отменено. Нажмите /start")