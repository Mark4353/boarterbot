from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.models import get_user_by_telegram_id
from app.keyboards import kb_nav_menu_help, kb_main_menu, kb_orders_list, kb_order_detail
from app.states import CreateOrder
from app.order_repo import create_order, list_orders_for_client, get_order_for_client

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

# ---------- create order flow ----------

@router.callback_query(F.data == "client:create_order")
async def create_order_start(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer("Нажмите /start", show_alert=True)
        return
    if user.role != "client":
        await call.answer("Создание заказа доступно только заказчику.", show_alert=True)
        return

    await state.clear()
    await state.set_state(CreateOrder.waiting_title)
    await call.answer()
    await send_clean_from_call(
        call,
        state,
        "Введите название заказа:",
        reply_markup=kb_nav_menu_help(back="order:back:menu"),
    )

@router.callback_query(F.data.startswith("order:back:"))
async def create_order_back(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer("Нажмите /start", show_alert=True)
        return
    if user.role != "client":
        await state.clear()
        await call.message.answer("Создание заказа доступно только заказчику.")
        await call.answer()
        return

    action = call.data.split(":")[-1]
    await call.answer()

    if action == "menu":
        await state.clear()
        await send_clean_from_call(
            call,
            state,
            "Меню:",
            reply_markup=kb_main_menu(user.role),
        )
        return

    if action == "title":
        await state.set_state(CreateOrder.waiting_title)
        await send_clean_from_call(
            call,
            state,
            "Введите название заказа:",
            reply_markup=kb_nav_menu_help(back="order:back:menu"),
        )
        return

    if action == "description":
        await state.set_state(CreateOrder.waiting_description)
        await send_clean_from_call(
            call,
            state,
            "Опишите задачу и требования (можно ссылкой):",
            reply_markup=kb_nav_menu_help(back="order:back:title"),
        )
        return

@router.callback_query(F.data == "order:cancel")
async def create_order_cancel(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer("Нажмите /start", show_alert=True)
        return

    await state.clear()
    await call.answer()
    await send_clean_from_call(
        call,
        state,
        "Ок, отменено.",
        reply_markup=kb_main_menu(user.role),
    )

@router.message(CreateOrder.waiting_title)
async def create_order_title(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    if user.role != "client":
        await state.clear()
        await message.answer("Создание заказа доступно только заказчику.")
        return

    title = (message.text or "").strip()
    await safe_delete_message(message)

    if not title:
        await send_clean(
            message,
            state,
            "Название не должно быть пустым. Введите название заказа:",
            reply_markup=kb_nav_menu_help(back="order:back:menu"),
        )
        return

    await state.update_data(title=title)
    await state.set_state(CreateOrder.waiting_description)
    await send_clean(
        message,
        state,
        "Опишите задачу и требования (можно ссылкой):",
        reply_markup=kb_nav_menu_help(back="order:back:title"),
    )

@router.message(CreateOrder.waiting_description)
async def create_order_description(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    if user.role != "client":
        await state.clear()
        await message.answer("Создание заказа доступно только заказчику.")
        return

    description = (message.text or "").strip()
    await safe_delete_message(message)

    if not description:
        await send_clean(
            message,
            state,
            "Описание не должно быть пустым. Опишите задачу:",
            reply_markup=kb_nav_menu_help(back="order:back:title"),
        )
        return

    await state.update_data(description=description)
    await state.set_state(CreateOrder.waiting_budget)
    await send_clean(
        message,
        state,
        "Укажите бюджет в долларах (число). Например: 50",
        reply_markup=kb_nav_menu_help(back="order:back:description"),
    )

@router.message(CreateOrder.waiting_budget)
async def create_order_budget(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    if user.role != "client":
        await state.clear()
        await message.answer("Создание заказа доступно только заказчику.")
        return

    raw = (message.text or "").strip()
    await safe_delete_message(message)

    if not raw.isdigit():
        await send_clean(
            message,
            state,
            "Бюджет должен быть числом. Например: 50",
            reply_markup=kb_nav_menu_help(back="order:back:description"),
        )
        return

    data = await state.get_data()
    order_id = await create_order(
        client_id=user.id,
        title=data.get("title", ""),
        description=data.get("description", ""),
        budget_minor=int(raw) * 100,
        currency="USD",
    )

    await state.clear()
    await clear_last_bot_message(state, message.bot, message.chat.id)

    await message.answer(
        f"✅ Заказ создан. Номер: #{order_id}",
        reply_markup=kb_main_menu(user.role),
    )

@router.callback_query(F.data == "client:my_orders")
async def my_orders(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer("Нажмите /start", show_alert=True)
        return
    if user.role != "client":
        await call.answer("Раздел доступен только заказчику.", show_alert=True)
        return

    orders = await list_orders_for_client(user.id, limit=10)
    if not orders:
        await call.message.answer("У вас пока нет заказов.", reply_markup=kb_main_menu(user.role))
        await call.answer()
        return

    text = "Ваши заказы:\n\nВыберите заказ для просмотра."
    await call.message.answer(text, reply_markup=kb_orders_list(orders))
    await call.answer()

@router.callback_query(F.data.startswith("order:view:"))
async def order_view(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer("Нажмите /start", show_alert=True)
        return
    if user.role != "client":
        await call.answer("Раздел доступен только заказчику.", show_alert=True)
        return

    try:
        order_id = int(call.data.split(":")[-1])
    except ValueError:
        await call.answer("Некорректный номер.", show_alert=True)
        return

    order = await get_order_for_client(order_id, user.id)
    if not order:
        await call.answer("Заказ не найден.", show_alert=True)
        return

    price = f"{int(order.get('budget_minor') or 0) / 100:.2f} {order.get('currency') or 'USD'}"
    created_at = order.get("created_at")
    created_label = created_at.strftime("%Y-%m-%d %H:%M") if created_at else "-"

    title = order.get("title") or "-"
    description = order.get("description") or "-"
    if len(description) > 1500:
        description = description[:1497] + "..."

    text = (
        f"Заказ #{order['id']}\n\n"
        f"Название: {title}\n"
        f"Описание: {description}\n"
        f"Бюджет: {price}\n"
        f"Статус: {order.get('status')}\n"
        f"Создан: {created_label}"
    )

    await call.message.answer(text, reply_markup=kb_order_detail(order_id))
    await call.answer()
