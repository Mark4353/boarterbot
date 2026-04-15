from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.models import get_user_by_telegram_id, get_user_by_id
from app.moderation_utils import get_moderator_ids
from app.states import Verify, VerifyChat
from app.profile_repo import get_editor_profile, set_editor_test_submission, set_editor_verification
from app.keyboards import kb_nav_menu_help, kb_editor_menu, kb_verify_chat_reply, kb_verify_chat_controls, kb_verify_admin
from app.moderation_utils import is_moderator_telegram_id
from app import texts

router = Router()

@router.callback_query(F.data == "verify:start")
async def verify_start(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer(texts.tr(None, "Type /start", "Натисніть /start"), show_alert=True)
        return
    if user.role != "editor":
        await call.answer(texts.tr(user.language, "Verification is available only for editors.", "Верифікація доступна лише монтажерам."), show_alert=True)
        return

    p = await get_editor_profile(user.id)
    status = (p.get("verification_status") if p else None) or "not_submitted"
    if status == "verified":
        await call.message.answer(texts.tr(user.language, "You are already verified.", "Ви вже верифіковані."), reply_markup=kb_editor_menu(True, user.language))
        await call.answer()
        return
    if status == "pending":
        await call.message.answer(texts.tr(user.language, "Your request is already submitted. Please wait.", "Заявку вже надіслано. Очікуйте відповіді."))
        await call.answer()
        return

    await state.clear()
    await state.set_state(Verify.waiting_submission)
    await call.answer()
    await call.message.answer(
        texts.tr(user.language, "Send verification info in one message (links, experience, examples).", "Опишіть дані для верифікації одним повідомленням (посилання, досвід, приклади робіт)."),
        reply_markup=kb_nav_menu_help(back="common:menu", lang=user.language),
    )

@router.message(Verify.waiting_submission)
async def verify_submit(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    if user.role != "editor":
        await state.clear()
        await message.answer(texts.tr(user.language, "Verification is available only for editors.", "Верифікація доступна лише монтажерам."))
        return

    submission = (message.text or "").strip()
    if not submission:
        await message.answer(texts.tr(user.language, "Send verification info in one message.", "Введіть дані для верифікації одним повідомленням."))
        return

    await set_editor_test_submission(user.id, submission)
    await state.clear()

    mods = list(get_moderator_ids())
    text = texts.tr(user.language, "New verification request\n", "Нова заявка на верифікацію\n")
    if message.from_user.username:
        text += texts.tr(user.language, f"User: @{message.from_user.username}\n", f"Юзер: @{message.from_user.username}\n")
    else:
        text += texts.tr(user.language, f"User ID: {message.from_user.id}\n", f"User ID: {message.from_user.id}\n")
    text += texts.tr(user.language, f"Details: {submission}", f"Дані: {submission}")

    if mods:
        for mod_id in mods:
            try:
                await message.bot.send_message(
                    mod_id,
                    text,
                    reply_markup=kb_verify_admin(user.id, None),
                )
            except:
                pass
        await message.answer(texts.tr(user.language, "Request sent to moderators.", "Заявку відправлено модераторам."), reply_markup=kb_editor_menu(False, user.language))
    else:
        await message.answer(texts.tr(user.language, "Moderators are not configured. Contact support.", "Модератори не налаштовані. Зверніться в підтримку."), reply_markup=kb_editor_menu(False, user.language))

@router.callback_query(F.data.startswith("verify:chat:reply:"))
async def verify_chat_reply(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer(texts.tr(None, "Type /start", "Натисніть /start"), show_alert=True)
        return

    try:
        moderator_user_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(texts.tr(user.language, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    await state.clear()
    await state.set_state(VerifyChat.chatting)
    await state.update_data(peer_user_id=moderator_user_id)
    await call.answer()
    await call.message.answer(texts.tr(user.language, "Chat with moderator. Send a message.", "Чат з модератором. Надсилайте повідомлення."), reply_markup=kb_verify_chat_controls(user.language))

@router.callback_query(F.data == "verify:chat:exit")
async def verify_chat_exit(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer(texts.tr(None, "Type /start", "Натисніть /start"), show_alert=True)
        return

    await state.clear()
    await call.answer()

    if user.role == "editor":
        p = await get_editor_profile(user.id)
        is_verified = bool(p and p.get("verification_status") == "verified")
        await call.message.answer(texts.tr(user.language, "Chat closed.", "Чат закрито."), reply_markup=kb_editor_menu(is_verified, user.language))
    else:
        await call.message.answer(texts.tr(user.language, "Chat closed.", "Чат закрито."))

@router.callback_query(F.data.startswith("verify:approve:"))
async def verify_approve(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer(texts.tr(None, "Type /start", "Натисніть /start"), show_alert=True)
        return
    if not is_moderator_telegram_id(call.from_user.id):
        await call.answer(texts.tr(user.language, "Access denied.", "Немає доступу."), show_alert=True)
        return

    try:
        editor_user_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(texts.tr(user.language, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    await set_editor_verification(editor_user_id, "verified", note="approved by moderator")
    editor = await get_user_by_id(editor_user_id)
    if editor:
        await call.bot.send_message(
            editor.telegram_id,
            texts.tr(editor.language, "✅ Your verification is approved.", "✅ Вашу верифікацію підтверджено."),
            reply_markup=kb_editor_menu(True, editor.language),
        )
    await call.answer(texts.tr(user.language, "✅ Approved.", "✅ Підтверджено."))

@router.callback_query(F.data.startswith("verify:reject:"))
async def verify_reject(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer(texts.tr(None, "Type /start", "Натисніть /start"), show_alert=True)
        return
    if not is_moderator_telegram_id(call.from_user.id):
        await call.answer(texts.tr(user.language, "Access denied.", "Немає доступу."), show_alert=True)
        return

    try:
        editor_user_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(texts.tr(user.language, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    await set_editor_verification(editor_user_id, "rejected", note="rejected by moderator")
    editor = await get_user_by_id(editor_user_id)
    if editor:
        await call.bot.send_message(
            editor.telegram_id,
            texts.tr(editor.language, "❌ Your verification was rejected.", "❌ Вашу верифікацію відхилено."),
            reply_markup=kb_editor_menu(False, editor.language),
        )
    await call.answer(texts.tr(user.language, "❌ Rejected.", "❌ Відхилено."))

@router.callback_query(F.data.startswith("verify:msg:"))
async def verify_message(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer(texts.tr(None, "Type /start", "Натисніть /start"), show_alert=True)
        return
    if not is_moderator_telegram_id(call.from_user.id):
        await call.answer(texts.tr(user.language, "Access denied.", "Немає доступу."), show_alert=True)
        return

    try:
        editor_user_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(texts.tr(user.language, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    await state.clear()
    await state.set_state(VerifyChat.chatting)
    await state.update_data(peer_user_id=editor_user_id)
    await call.answer()
    await call.message.answer(
        texts.tr(user.language, "Chat with editor. Send a message.", "Чат з монтажером. Надсилайте повідомлення."),
        reply_markup=kb_verify_chat_controls(user.language),
    )

@router.message(VerifyChat.chatting)
async def verify_chat_message(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return

    text = (message.text or "").strip()
    if not text:
        return

    data = await state.get_data()
    peer_user_id = int(data.get("peer_user_id") or 0)
    if not peer_user_id:
        await state.clear()
        return

    peer = await get_user_by_id(peer_user_id)
    if not peer:
        await state.clear()
        return

    await message.bot.send_message(
        peer.telegram_id,
        texts.tr(
            user.language,
            f"Verification message from {user.display_name or user.username or f'id:{user.telegram_id}'}:\n{text}",
            f"Повідомлення по верифікації від {user.display_name or user.username or f'id:{user.telegram_id}'}:\n{text}",
        ),
        reply_markup=kb_verify_chat_controls(user.language),
    )

