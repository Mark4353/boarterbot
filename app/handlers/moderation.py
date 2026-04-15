from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.models import get_user_by_telegram_id, get_user_by_id
from app.profile_repo import set_editor_verification
from app.menu_utils import get_menu_markup_for_user
from app.moderation_utils import is_moderator_telegram_id
from app.order_repo import list_active_deals, get_order_by_id, set_payment_status, create_deal_message, add_to_balance
from app.moderation_repo import (
    list_pending_verifications,
    list_held_messages,
    list_dispute_deals,
    get_deal_by_id,
    get_held_message_by_id,
    update_held_message_status,
    create_held_message,
    count_stats,
    create_user_sanction,
    log_moderation_action,
)
from app.keyboards import (
    kb_mod_verification_controls,
    kb_mod_held_controls,
    kb_mod_dispute_controls,
    kb_mod_user_controls,
    kb_moderation_menu,
    kb_nav_menu_help,
    kb_verify_chat_reply,
    kb_verify_chat_controls,
    kb_deals_list,
    kb_mod_deal_menu,
    kb_mod_deal_payment_menu,
)
from app.states import ModerationSearch, ModerationUserLookup, ModerationMessage, ModerationRefund, VerifyChat
from app.payment_api import refund_payment
from app import texts

router = Router()

# ---------- helpers ----------

def _truncate(text: str | None, limit: int = 600) -> str:
    if not text:
        return "—"
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."

def _money_from_minor(minor: int, currency: str = "USD") -> str:
    return f"{minor / 100:.2f} {currency}"

def _t(user, en: str, ua: str) -> str:
    return texts.tr(getattr(user, "language", None), en, ua)

async def _ensure_moderator(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer(texts.tr(None, "Type /start", "Натисніть /start"), show_alert=True)
        return None
    if not is_moderator_telegram_id(call.from_user.id):
        await call.answer(_t(user, "Access denied", "Немає доступу"), show_alert=True)
        return None
    return user

async def _ensure_moderator_message(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or not is_moderator_telegram_id(message.from_user.id):
        return None
    return user

async def _safe_edit_or_send(call: CallbackQuery, text: str, reply_markup=None):
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except:
        await call.message.answer(text, reply_markup=reply_markup)

async def _show_pending_verifications(call: CallbackQuery, offset: int, lang: str | None = None):
    items = await list_pending_verifications(offset=offset, limit=1)
    if not items:
        await _safe_edit_or_send(
            call,
            texts.tr(lang, "🆕 New verifications\n\nQueue is empty.", "🆕 Нові верифікації\n\nЧерга порожня."),
            reply_markup=kb_nav_menu_help(back="common:menu", lang=lang),
        )
        return

    p = items[0]
    price = _money_from_minor(int(p.get("price_from_minor") or 0))
    name_label = texts.tr(lang, "name", "ім'я")
    skills_label = texts.tr(lang, "skills", "спеціалізація")
    price_label = texts.tr(lang, "price", "ціна")
    portfolio_label = texts.tr(lang, "portfolio", "портфоліо")
    text = (
        texts.tr(lang, "🆕 New verifications\n\n", "🆕 Нові верифікації\n\n") +
        f"user_id: {p.get('user_id')}\n"
        f"{name_label}: {p.get('name') or '?'}\n"
        f"{skills_label}: {p.get('skills') or '?'}\n"
        f"{price_label}: {price}\n"
        f"{portfolio_label}: {p.get('portfolio_url') or '?'}\n"
        f"test_submission: {_truncate(p.get('test_submission'))}\n"
        f"verification_status: {p.get('verification_status')}"
    )
    await _safe_edit_or_send(
        call,
        text,
        reply_markup=kb_mod_verification_controls(int(p["user_id"]), offset, lang),
    )

async def _show_held_messages(call: CallbackQuery, offset: int, lang: str | None = None):
    items = await list_held_messages(offset=offset, limit=1)
    if not items:
        await _safe_edit_or_send(
            call,
            texts.tr(lang, "💬 Messages on review\n\nQueue is empty.", "💬 Повідомлення на перевірці\n\nЧерга порожня."),
            reply_markup=kb_nav_menu_help(back="common:menu", lang=lang),
        )
        return

    m = items[0]
    text = (
        texts.tr(lang, "💬 Messages on review\n\n", "💬 Повідомлення на перевірці\n\n") +
        f"deal_id: {m.get('deal_id')}\n"
        f"sender_user_id: {m.get('sender_user_id')}\n"
        f"original_text: {_truncate(m.get('original_text'))}\n"
        f"normalized_text: {_truncate(m.get('normalized_text'))}\n"
        f"flag_reason: {m.get('flag_reason')}"
    )
    await _safe_edit_or_send(
        call,
        text,
        reply_markup=kb_mod_held_controls(int(m["id"]), offset, lang),
    )

async def _show_disputes(call: CallbackQuery, offset: int, lang: str | None = None):
    items = await list_dispute_deals(offset=offset, limit=1)
    if not items:
        await _safe_edit_or_send(
            call,
            texts.tr(lang, "⚠️ Disputes\n\nNo active disputes.", "⚠️ Спори\n\nАктивних спорів немає."),
            reply_markup=kb_nav_menu_help(back="common:menu", lang=lang),
        )
        return

    d = items[0]
    text = (
        texts.tr(lang, "⚠️ Disputes\n\n", "⚠️ Спори\n\n") +
        f"deal_id: {d.get('id')}\n"
        f"client_id: {d.get('client_id')}\n"
        f"editor_id: {d.get('editor_id')}\n"
        f"status: {d.get('status')}\n"
        f"price_minor: {d.get('price_minor')}"
    )
    await _safe_edit_or_send(
        call,
        text,
        reply_markup=kb_mod_dispute_controls(int(d["id"]), offset, lang),
    )

async def _show_active_deals(call: CallbackQuery, lang: str | None = None):
    items = await list_active_deals(limit=20)
    if not items:
        await _safe_edit_or_send(
            call,
            texts.tr(lang, "💼 Active deals\n\nNo active deals found.", "💼 Активні угоди\n\nАктивних угод не знайдено."),
            reply_markup=kb_nav_menu_help(back="common:menu", lang=lang),
        )
        return

    await _safe_edit_or_send(
        call,
        texts.tr(lang, "💼 Active deals:", "💼 Активні угоди:"),
        reply_markup=kb_deals_list(items, lang),
    )

# ---------- menu entries ----------

@router.callback_query(F.data == "mod:menu")
async def mod_menu(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    await _safe_edit_or_send(
        call,
        _t(user, "Moderator tools:", "Інструменти модератора:"),
        reply_markup=kb_moderation_menu(user.language),
    )
    await call.answer()

@router.callback_query(F.data == "mod:verifications")
async def mod_verifications(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    await _show_pending_verifications(call, 0, user.language)
    await call.answer()

@router.callback_query(F.data.startswith("mod:verifications:page:"))
async def mod_verifications_page(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        offset = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid offset.", "Некоректний offset."), show_alert=True)
        return
    await _show_pending_verifications(call, offset, user.language)
    await call.answer()

@router.callback_query(F.data.startswith("mod:verifications:approve:"))
async def mod_verifications_approve(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    parts = call.data.split(":")
    if len(parts) < 5:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return
    try:
        editor_user_id = int(parts[3])
        offset = int(parts[4])
    except ValueError:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    await set_editor_verification(editor_user_id, "verified", note="approved by moderator")
    await log_moderation_action(
        moderator_user_id=user.id,
        action_type="verify_approve",
        target_user_id=editor_user_id,
        object_type="editor_profile",
        object_id=editor_user_id,
        payload={},
    )
    await _show_pending_verifications(call, offset, user.language)
    await call.answer(_t(user, "✅ Approved.", "✅ Підтверджено."))

@router.callback_query(F.data.startswith("mod:verifications:reject:"))
async def mod_verifications_reject(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    parts = call.data.split(":")
    if len(parts) < 5:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return
    try:
        editor_user_id = int(parts[3])
        offset = int(parts[4])
    except ValueError:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    await set_editor_verification(editor_user_id, "rejected", note="rejected by moderator")
    await log_moderation_action(
        moderator_user_id=user.id,
        action_type="verify_reject",
        target_user_id=editor_user_id,
        object_type="editor_profile",
        object_id=editor_user_id,
        payload={},
    )
    await _show_pending_verifications(call, offset, user.language)
    await call.answer(_t(user, "❌ Rejected.", "❌ Відхилено."))

@router.callback_query(F.data.startswith("mod:verifications:chat:"))
async def mod_verifications_chat(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        editor_user_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid user_id.", "Некоректний user_id."), show_alert=True)
        return

    await state.clear()
    await state.set_state(VerifyChat.chatting)
    await state.update_data(peer_user_id=editor_user_id)

    await _safe_edit_or_send(
        call,
        _t(user, "Chat with editor. Send a message.", "Чат з монтажером. Надішліть повідомлення."),
        reply_markup=kb_verify_chat_controls(user.language),
    )
    await call.answer()

    editor = await get_user_by_id(editor_user_id)
    if editor:
        await call.bot.send_message(
            editor.telegram_id,
            _t(user, "Moderator is waiting for your verification message. You can reply here.", "Модератор очікує ваше повідомлення по верифікації. Ви можете відповісти тут."),
            reply_markup=kb_verify_chat_reply(user.id, user.language),
        )

@router.callback_query(F.data.startswith("mod:verifications:msg:"))
async def mod_verifications_message(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        target_user_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid user_id.", "Некоректний user_id."), show_alert=True)
        return

    await state.clear()
    await state.set_state(ModerationMessage.waiting_text)
    await state.update_data(
        target_user_ids=[target_user_id],
        object_type="editor_profile",
        object_id=target_user_id,
        action_type="verification_message",
    )
    await _safe_edit_or_send(
        call,
        _t(user, "✉️ Send a single message to the user:", "✉️ Напишіть повідомлення користувачу одним повідомленням:"),
        reply_markup=kb_nav_menu_help(back="common:menu", lang=user.language),
    )
    await call.answer()

@router.callback_query(F.data == "mod:held_messages")
async def mod_held_messages(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    await _show_held_messages(call, 0, user.language)
    await call.answer()

@router.callback_query(F.data.startswith("mod:held_messages:page:"))
async def mod_held_messages_page(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        offset = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid offset.", "Некоректний offset."), show_alert=True)
        return
    await _show_held_messages(call, offset, user.language)
    await call.answer()

@router.callback_query(F.data.startswith("mod:held_messages:approve:"))
async def mod_held_messages_approve(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    parts = call.data.split(":")
    if len(parts) < 5:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return
    try:
        message_id = int(parts[3])
        offset = int(parts[4])
    except ValueError:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    held = await get_held_message_by_id(message_id)
    await update_held_message_status(message_id, "approved")
    await log_moderation_action(
        moderator_user_id=user.id,
        action_type="held_approve",
        target_user_id=int(held["sender_user_id"]) if held else None,
        object_type="held_message",
        object_id=message_id,
        payload={},
    )
    await _show_held_messages(call, offset, user.language)
    await call.answer(_t(user, "✅ Approved.", "✅ Підтверджено."))

@router.callback_query(F.data.startswith("mod:held_messages:reject:"))
async def mod_held_messages_reject(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    parts = call.data.split(":")
    if len(parts) < 5:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return
    try:
        message_id = int(parts[3])
        offset = int(parts[4])
    except ValueError:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    held = await get_held_message_by_id(message_id)
    await update_held_message_status(message_id, "rejected")
    await log_moderation_action(
        moderator_user_id=user.id,
        action_type="held_reject",
        target_user_id=int(held["sender_user_id"]) if held else None,
        object_type="held_message",
        object_id=message_id,
        payload={},
    )
    await _show_held_messages(call, offset, user.language)
    await call.answer(_t(user, "❌ Rejected.", "❌ Відхилено."))

@router.callback_query(F.data.startswith("mod:held_messages:ban:"))
async def mod_held_messages_ban(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    parts = call.data.split(":")
    if len(parts) < 5:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return
    try:
        message_id = int(parts[3])
        offset = int(parts[4])
    except ValueError:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    held = await get_held_message_by_id(message_id)
    if not held:
        await call.answer(_t(user, "Message not found.", "Повідомлення не знайдено."), show_alert=True)
        return

    target_user_id = int(held["sender_user_id"])
    await create_user_sanction(
        target_user_id=target_user_id,
        moderator_user_id=user.id,
        sanction_type="ban",
        reason="held_message",
    )
    await update_held_message_status(message_id, "rejected")
    await log_moderation_action(
        moderator_user_id=user.id,
        action_type="user_ban",
        target_user_id=target_user_id,
        object_type="held_message",
        object_id=message_id,
        payload={"reason": "held_message"},
    )
    await _show_held_messages(call, offset, user.language)
    await call.answer(_t(user, "🚫 User banned.", "🚫 Користувача заблоковано."))

@router.callback_query(F.data.startswith("mod:held_messages:msg:"))
async def mod_held_messages_message(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        message_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    held = await get_held_message_by_id(message_id)
    if not held:
        await call.answer(_t(user, "Message not found.", "Повідомлення не знайдено."), show_alert=True)
        return

    await state.clear()
    await state.set_state(ModerationMessage.waiting_text)
    await state.update_data(
        target_user_ids=[int(held["sender_user_id"])],
        object_type="held_message",
        object_id=message_id,
        action_type="held_message_reply",
    )
    await _safe_edit_or_send(
        call,
        _t(user, "✉️ Send a single message to the user:", "✉️ Напишіть повідомлення користувачу одним повідомленням:"),
        reply_markup=kb_nav_menu_help(back="common:menu", lang=user.language),
    )
    await call.answer()

@router.callback_query(F.data == "mod:disputes")
async def mod_disputes(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    await _show_disputes(call, 0, user.language)
    await call.answer()

@router.callback_query(F.data.startswith("mod:disputes:page:"))
async def mod_disputes_page(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        offset = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid offset.", "Некоректний offset."), show_alert=True)
        return
    await _show_disputes(call, offset, user.language)
    await call.answer()

@router.callback_query(F.data == "mod:active_deals")
async def mod_active_deals(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    await _show_active_deals(call, user.language)
    await call.answer()

@router.callback_query(F.data.startswith("mod:deal:menu:"))
async def mod_deal_menu(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        order_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid order id.", "Некоректний id угоди."), show_alert=True)
        return

    order = await get_order_by_id(order_id)
    if not order:
        await call.answer(_t(user, "Deal not found.", "Угоду не знайдено."), show_alert=True)
        return

    is_dispute = order.get("status") == "dispute"
    await _safe_edit_or_send(
        call,
        _t(user, "Deal menu:", "Меню угоди:"),
        reply_markup=kb_mod_deal_menu(order_id, is_dispute, order.get("payment_status"), user.language),
    )
    await call.answer()

@router.callback_query(F.data.startswith("mod:deal:payment:"))
async def mod_deal_payment(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        order_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid order id.", "Некоректний id угоди."), show_alert=True)
        return

    await _safe_edit_or_send(
        call,
        _t(user, "Deal payment actions:", "Дії з оплатою угоди:"),
        reply_markup=kb_mod_deal_payment_menu(order_id, user.language),
    )
    await call.answer()

@router.callback_query(F.data.startswith("mod:deal:chat:client:"))
async def mod_deal_chat_client(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        order_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid order id.", "Некоректний id угоди."), show_alert=True)
        return

    order = await get_order_by_id(order_id)
    if not order or not order.get("client_id"):
        await call.answer(_t(user, "Client not found.", "Замовника не знайдено."), show_alert=True)
        return

    await state.clear()
    await state.set_state(ModerationMessage.waiting_text)
    await state.update_data(
        target_user_ids=[int(order["client_id"])],
        object_type="deal",
        object_id=order_id,
        action_type="mod_chat_client",
    )
    await _safe_edit_or_send(
        call,
        _t(user, "✉️ Send a single message to the client:", "✉️ Напишіть повідомлення замовнику одним повідомленням:"),
        reply_markup=kb_nav_menu_help(back=f"mod:deal:menu:{order_id}", lang=user.language),
    )
    await call.answer()

@router.callback_query(F.data.startswith("mod:deal:chat:editor:"))
async def mod_deal_chat_editor(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        order_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid order id.", "Некоректний id угоди."), show_alert=True)
        return

    order = await get_order_by_id(order_id)
    if not order or not order.get("editor_id"):
        await call.answer(_t(user, "Editor not found.", "Монтажера не знайдено."), show_alert=True)
        return

    await state.clear()
    await state.set_state(ModerationMessage.waiting_text)
    await state.update_data(
        target_user_ids=[int(order["editor_id"])],
        object_type="deal",
        object_id=order_id,
        action_type="mod_chat_editor",
    )
    await _safe_edit_or_send(
        call,
        _t(user, "✉️ Send a single message to the editor:", "✉️ Напишіть повідомлення монтажеру одним повідомленням:"),
        reply_markup=kb_nav_menu_help(back=f"mod:deal:menu:{order_id}", lang=user.language),
    )
    await call.answer()

@router.callback_query(F.data.startswith("mod:deal:refund:client:"))
async def mod_deal_refund_client(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        order_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid order id.", "Некоректний id угоди."), show_alert=True)
        return

    order = await get_order_by_id(order_id)
    if not order or not order.get("client_id"):
        await call.answer(_t(user, "Client not found.", "Замовника не знайдено."), show_alert=True)
        return

    await state.clear()
    await state.set_state(ModerationMessage.waiting_text)
    await state.update_data(
        target_user_ids=[int(order["client_id"])],
        object_type="deal",
        object_id=order_id,
        action_type="refund_client",
        action_payload={"payment_status": "refunded_client", "refund_target": "client"},
    )
    await _safe_edit_or_send(
        call,
        _t(user, "✉️ Enter a short reason for refunding the client:", "✉️ Введіть коротку причину повернення коштів замовнику:"),
        reply_markup=kb_nav_menu_help(back=f"mod:deal:payment:{order_id}", lang=user.language),
    )
    await call.answer()

@router.callback_query(F.data.startswith("mod:deal:refund:partial:"))
async def mod_deal_refund_partial(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        order_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid order id.", "Некоректний id угоди."), show_alert=True)
        return

    order = await get_order_by_id(order_id)
    if not order or not order.get("client_id"):
        await call.answer(_t(user, "Client not found.", "Замовника не знайдено."), show_alert=True)
        return

    await state.clear()
    await state.set_state(ModerationRefund.waiting_amount)
    await state.update_data(order_id=order_id)
    await _safe_edit_or_send(
        call,
        _t(user, "💰 Enter partial refund amount (USD):", "💰 Введіть суму часткового повернення (USD):"),
        reply_markup=kb_nav_menu_help(back=f"mod:deal:payment:{order_id}", lang=user.language),
    )
    await call.answer()

@router.callback_query(F.data.startswith("mod:deal:refund:editor:"))
async def mod_deal_refund_editor(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        order_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid order id.", "Некоректний id угоди."), show_alert=True)
        return

    order = await get_order_by_id(order_id)
    if not order or not order.get("editor_id"):
        await call.answer(_t(user, "Editor not found.", "Монтажера не знайдено."), show_alert=True)
        return

    await state.clear()
    await state.set_state(ModerationMessage.waiting_text)
    await state.update_data(
        target_user_ids=[int(order["editor_id"])],
        object_type="deal",
        object_id=order_id,
        action_type="refund_editor",
        action_payload={"payment_status": "refunded_editor"},
    )
    await _safe_edit_or_send(
        call,
        _t(user, "✉️ Enter a short reason for refunding the editor:", "✉️ Введіть коротку причину повернення коштів монтажеру:"),
        reply_markup=kb_nav_menu_help(back=f"mod:deal:payment:{order_id}", lang=user.language),
    )
    await call.answer()

@router.callback_query(F.data.startswith("mod:deal:split:"))
async def mod_deal_split(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        order_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid order id.", "Некоректний id угоди."), show_alert=True)
        return

    order = await get_order_by_id(order_id)
    if not order or not (order.get("client_id") and order.get("editor_id")):
        await call.answer(_t(user, "Deal parties not found.", "Учасники угоди не знайдені."), show_alert=True)
        return

    await state.clear()
    await state.set_state(ModerationMessage.waiting_text)
    await state.update_data(
        target_user_ids=[int(order["client_id"]), int(order["editor_id"])],
        object_type="deal",
        object_id=order_id,
        action_type="split_payment",
        action_payload={"payment_status": "split_50_50", "refund_target": "split"},
    )
    await _safe_edit_or_send(
        call,
        _t(user, "✉️ Enter a short explanation for the 50/50 split:", "✉️ Введіть коротку причину розподілу 50/50:"),
        reply_markup=kb_nav_menu_help(back=f"mod:deal:payment:{order_id}", lang=user.language),
    )
    await call.answer()

@router.callback_query(F.data.startswith("mod:disputes:pay:"))
async def mod_disputes_pay(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    parts = call.data.split(":")
    if len(parts) < 5:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return
    try:
        deal_id = int(parts[3])
        offset = int(parts[4])
    except ValueError:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    await log_moderation_action(
        moderator_user_id=user.id,
        action_type="dispute_pay_editor",
        target_user_id=None,
        object_type="deal",
        object_id=deal_id,
        payload={},
    )
    await _show_disputes(call, offset, user.language)
    await call.answer(_t(user, "✅ Decision recorded.", "✅ Рішення записано."))

@router.callback_query(F.data.startswith("mod:disputes:refund:"))
async def mod_disputes_refund(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    parts = call.data.split(":")
    if len(parts) < 5:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return
    try:
        deal_id = int(parts[3])
        offset = int(parts[4])
    except ValueError:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    await log_moderation_action(
        moderator_user_id=user.id,
        action_type="dispute_refund_client",
        target_user_id=None,
        object_type="deal",
        object_id=deal_id,
        payload={},
    )
    await _show_disputes(call, offset, user.language)
    await call.answer(_t(user, "↩️ Decision recorded.", "↩️ Рішення записано."))

@router.callback_query(F.data.startswith("mod:disputes:msg:"))
async def mod_disputes_message(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    try:
        deal_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(user, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    deal = await get_deal_by_id(deal_id)
    if not deal:
        await call.answer(_t(user, "Deal not found.", "Угоду не знайдено."), show_alert=True)
        return

    targets = []
    if deal.get("client_id"):
        targets.append(int(deal["client_id"]))
    if deal.get("editor_id"):
        targets.append(int(deal["editor_id"]))

    await state.clear()
    await state.set_state(ModerationMessage.waiting_text)
    await state.update_data(
        target_user_ids=targets,
        object_type="deal",
        object_id=deal_id,
        action_type="dispute_message",
    )
    await _safe_edit_or_send(
        call,
        _t(user, "✉️ Send a single message to dispute parties:", "✉️ Напишіть повідомлення сторонам спору одним повідомленням:"),
        reply_markup=kb_nav_menu_help(back="common:menu", lang=user.language),
    )
    await call.answer()

@router.callback_query(F.data == "mod:search")
async def mod_search_start(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    await state.clear()
    await state.set_state(ModerationSearch.waiting_query)
    await _safe_edit_or_send(
        call,
        _t(user, "🔎 Search\n\nEnter user_id or deal_id:", "🔎 Пошук\n\nВведіть user_id або deal_id:"),
        reply_markup=kb_nav_menu_help(back="common:menu", lang=user.language),
    )
    await call.answer()

@router.message(ModerationSearch.waiting_query)
async def mod_search_result(message: Message, state: FSMContext):
    user = await _ensure_moderator_message(message)
    if not user:
        await state.clear()
        return

    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(_t(user, "Enter a number (user_id or deal_id).", "Введіть число (user_id або deal_id)."))
        return

    query_id = int(raw)
    found_user = await get_user_by_id(query_id)
    found_deal = await get_deal_by_id(query_id)

    lines = [_t(user, "🔎 Search", "🔎 Пошук")]
    if found_user:
        username = f"@{found_user.username}" if found_user.username else "—"
        lines.append(
            _t(user, "\nUser:", "\nКористувач:") +
            f"\n  user_id: {found_user.id}"
            f"\n  telegram_id: {found_user.telegram_id}"
            f"\n  username: {username}"
            f"\n  display_name: {found_user.display_name or '—'}"
            f"\n  role: {found_user.role}"
        )
    if found_deal:
        lines.append(
            _t(user, "\nDeal:", "\nУгода:") +
            f"\n  deal_id: {found_deal.get('id')}"
            f"\n  client_id: {found_deal.get('client_id')}"
            f"\n  editor_id: {found_deal.get('editor_id')}"
            f"\n  status: {found_deal.get('status')}"
            f"\n  price_minor: {found_deal.get('price_minor')}"
        )

    if not found_user and not found_deal:
        lines.append(_t(user, "\nNothing found.", "\nНічого не знайдено."))

    await state.clear()
    await message.answer("\n".join(lines), reply_markup=await get_menu_markup_for_user(user))

@router.callback_query(F.data == "mod:stats")
async def mod_stats(call: CallbackQuery):
    user = await _ensure_moderator(call)
    if not user:
        return
    stats = await count_stats()
    text = (
        _t(user, "📊 Stats\n\n", "📊 Статистика\n\n") +
        f"{_t(user, 'pending verifications', 'очікують верифікації')}: {stats.get('pending_verifications', 0)}\n"
        f"{_t(user, 'held messages', 'повідомлення на перевірці')}: {stats.get('held_messages', 0)}\n"
        f"{_t(user, 'disputes', 'спори')}: {stats.get('disputes', 0)}\n"
        f"{_t(user, 'users', 'користувачі')}: {stats.get('users', 0)}\n"
        f"{_t(user, 'editor profiles', 'профілі монтажерів')}: {stats.get('editor_profiles', 0)}\n"
        f"{_t(user, 'client profiles', 'профілі замовників')}: {stats.get('client_profiles', 0)}"
    )
    await _safe_edit_or_send(call, text, reply_markup=kb_nav_menu_help(back="common:menu", lang=user.language))
    await call.answer()

@router.callback_query(F.data == "mod:users")
async def mod_users_start(call: CallbackQuery, state: FSMContext):
    user = await _ensure_moderator(call)
    if not user:
        return
    await state.clear()
    await state.set_state(ModerationUserLookup.waiting_user_id)
    await _safe_edit_or_send(
        call,
        _t(user, "🚫 Users / sanctions\n\nEnter user_id:", "🚫 Користувачі / санкції\n\nВведіть user_id:"),
        reply_markup=kb_nav_menu_help(back="common:menu", lang=user.language),
    )
    await call.answer()

@router.message(ModerationUserLookup.waiting_user_id)
async def mod_users_show(message: Message, state: FSMContext):
    moderator = await _ensure_moderator_message(message)
    if not moderator:
        await state.clear()
        return

    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(_t(moderator, "Enter a number (user_id).", "Введіть число (user_id)."))
        return

    user_id = int(raw)
    user = await get_user_by_id(user_id)
    if not user:
        await message.answer(_t(moderator, "User not found.", "Користувача не знайдено."))
        return

    text = (
        _t(moderator, "🚫 User\n\n", "🚫 Користувач\n\n") +
        f"user_id: {user.id}\n"
        f"telegram_id: {user.telegram_id}\n"
        f"username: {('@' + user.username) if user.username else '—'}\n"
        f"display_name: {user.display_name or '—'}\n"
        f"role: {user.role}"
    )
    await state.clear()
    await message.answer(text, reply_markup=kb_mod_user_controls(user.id, moderator.language))

@router.callback_query(F.data.startswith("mod:user:warn:"))
async def mod_user_warn(call: CallbackQuery):
    moderator = await _ensure_moderator(call)
    if not moderator:
        return
    try:
        target_user_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(moderator, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    await create_user_sanction(
        target_user_id=target_user_id,
        moderator_user_id=moderator.id,
        sanction_type="warning",
        reason="manual_warning",
    )
    await log_moderation_action(
        moderator_user_id=moderator.id,
        action_type="user_warning",
        target_user_id=target_user_id,
        object_type="user",
        object_id=target_user_id,
        payload={"reason": "manual_warning"},
    )
    await _safe_edit_or_send(
        call,
        _t(moderator, f"⚠️ Warning issued to user {target_user_id}.", f"⚠️ Попередження видано користувачу {target_user_id}."),
        reply_markup=kb_mod_user_controls(target_user_id, moderator.language),
    )
    await call.answer()

@router.callback_query(F.data.startswith("mod:user:ban:"))
async def mod_user_ban(call: CallbackQuery):
    moderator = await _ensure_moderator(call)
    if not moderator:
        return
    try:
        target_user_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(moderator, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    await create_user_sanction(
        target_user_id=target_user_id,
        moderator_user_id=moderator.id,
        sanction_type="ban",
        reason="manual_ban",
    )
    await log_moderation_action(
        moderator_user_id=moderator.id,
        action_type="user_ban",
        target_user_id=target_user_id,
        object_type="user",
        object_id=target_user_id,
        payload={"reason": "manual_ban"},
    )
    await _safe_edit_or_send(
        call,
        _t(moderator, f"🚫 User {target_user_id} banned.", f"🚫 Користувача {target_user_id} заблоковано."),
        reply_markup=kb_mod_user_controls(target_user_id, moderator.language),
    )
    await call.answer()

@router.callback_query(F.data.startswith("mod:user:msg:"))
async def mod_user_message(call: CallbackQuery, state: FSMContext):
    moderator = await _ensure_moderator(call)
    if not moderator:
        return
    try:
        target_user_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer(_t(moderator, "Invalid data.", "Невірні дані."), show_alert=True)
        return

    await state.clear()
    await state.set_state(ModerationMessage.waiting_text)
    await state.update_data(
        target_user_ids=[target_user_id],
        object_type="user",
        object_id=target_user_id,
        action_type="user_message",
    )
    await _safe_edit_or_send(
        call,
        _t(moderator, "✉️ Send a single message to the user:", "✉️ Напишіть повідомлення користувачу одним повідомленням:"),
        reply_markup=kb_nav_menu_help(back="common:menu", lang=moderator.language),
    )
    await call.answer()

@router.message(ModerationRefund.waiting_amount)
async def mod_refund_amount(message: Message, state: FSMContext):
    moderator = await _ensure_moderator_message(message)
    if not moderator:
        await state.clear()
        return

    raw = (message.text or "").strip().replace(",", ".")
    try:
        amount = float(raw)
        if amount <= 0:
            raise ValueError()
        amount_minor = int(round(amount * 100))
    except ValueError:
        await message.answer(_t(moderator, "Enter a valid amount (e.g., 25.50).", "Введіть коректну суму (наприклад, 25.50)."))
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await state.clear()
        await message.answer(_t(moderator, "Session expired. Please try again.", "Сесія закінчилась. Спробуйте ще раз."))
        return

    order = await get_order_by_id(int(order_id))
    if not order:
        await state.clear()
        await message.answer(_t(moderator, "Deal not found.", "Угоду не знайдено."))
        return

    max_amount = int(order.get("agreed_price_minor") or 0)
    if amount_minor > max_amount:
        await message.answer(_t(moderator, "Amount exceeds deal price.", "Сума перевищує ціну угоди."))
        return

    await state.clear()
    await state.set_state(ModerationMessage.waiting_text)
    await state.update_data(
        target_user_ids=[int(order["client_id"])],
        object_type="deal",
        object_id=int(order_id),
        action_type="refund_client_partial",
        action_payload={
            "payment_status": "refunded_partial",
            "refund_target": "client",
            "refund_amount_minor": amount_minor,
        },
    )
    await message.answer(
        _t(moderator, "✉️ Enter a short reason for the partial refund:", "✉️ Введіть коротку причину часткового повернення:"),
        reply_markup=kb_nav_menu_help(back=f"mod:deal:payment:{order_id}", lang=moderator.language),
    )

@router.message(ModerationMessage.waiting_text)
async def mod_send_message(message: Message, state: FSMContext):
    moderator = await _ensure_moderator_message(message)
    if not moderator:
        await state.clear()
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer(_t(moderator, "Enter message text.", "Введіть текст повідомлення."))
        return

    data = await state.get_data()
    target_ids = list({int(x) for x in (data.get("target_user_ids") or [])})
    object_type = data.get("object_type") or "user"
    object_id = data.get("object_id")
    action_type = data.get("action_type") or "message"
    action_payload = data.get("action_payload") or {}

    for target_id in target_ids:
        target_user = await get_user_by_id(target_id)
        if target_user:
            await message.bot.send_message(
                target_user.telegram_id,
                _t(moderator, f"Moderator note:\n{text}", f"Нотатка модератора:\n{text}"),
            )

    if object_type == "deal" and object_id:
        await create_deal_message(int(object_id), moderator.id, "moderator", text)
    if object_type == "deal" and action_payload.get("payment_status") and object_id:
        order = await get_order_by_id(int(object_id))
        if not order:
            await state.clear()
            await message.answer(_t(moderator, "Deal not found.", "Угоду не знайдено."))
            return

        refund_target = action_payload.get("refund_target")
        refund_amount_minor = action_payload.get("refund_amount_minor")
        if refund_target in {"client", "split"}:
            payment_order_id = order.get("stripe_session_id")
            if not payment_order_id:
                await state.clear()
                await message.answer(_t(moderator, "Payment ID is missing for this deal.", "Відсутній ідентифікатор оплати для цієї угоди."))
                return

            if refund_amount_minor is None:
                total_amount = int(order.get("agreed_price_minor") or 0)
                refund_amount_minor = total_amount if refund_target == "client" else total_amount // 2

            refund_result = await refund_payment(
                order_id=str(payment_order_id),
                amount_minor=int(refund_amount_minor),
                currency=order.get("currency") or "USD",
            )
            refund_status = str(refund_result.get("status", "")).lower() if refund_result else ""
            if not refund_result or refund_status in {"error", "failure"}:
                await state.clear()
                await message.answer(_t(moderator, "Refund failed. Please check LiqPay.", "Повернення не вдалося. Перевірте LiqPay."))
                return

        await set_payment_status(int(object_id), action_payload["payment_status"])

        # Handle balance adjustments for refunds and splits
        payment_status = action_payload["payment_status"]
        if payment_status == "refunded_client":
            # Refund to client - no balance change needed as money goes back to payment system
            pass
        elif payment_status == "refunded_editor":
            # Refund to editor - deduct from our balance if they were already paid
            if order.get("payment_status") == "paid":
                editor_id = order.get("editor_id")
                amount = order.get("agreed_price_minor", 0)
                if editor_id and amount > 0:
                    await add_to_balance(editor_id, -amount, "refunded", int(object_id), f"Refunded by moderator: {text}")
        elif payment_status == "split_50_50":
            # Split payment - credit both parties with half
            client_id = order.get("client_id")
            editor_id = order.get("editor_id")
            total_amount = order.get("agreed_price_minor", 0)
            half_amount = total_amount // 2

            if client_id and editor_id and total_amount > 0:
                # Credit client half
                await add_to_balance(client_id, half_amount, "split_refund", int(object_id), f"50/50 split by moderator: {text}")
                # Credit editor half
                await add_to_balance(editor_id, half_amount, "split_payment", int(object_id), f"50/50 split by moderator: {text}")

    await log_moderation_action(
        moderator_user_id=moderator.id,
        action_type=action_type,
        target_user_id=target_ids[0] if target_ids else None,
        object_type=object_type,
        object_id=int(object_id) if object_id else None,
        payload={"text": text, "targets": target_ids, **action_payload},
    )

    await state.clear()
    await message.answer(_t(moderator, "✅ Message sent.", "✅ Повідомлення надіслано."), reply_markup=await get_menu_markup_for_user(moderator))
