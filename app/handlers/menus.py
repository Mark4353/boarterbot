from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import os

from app.states import BalanceWithdraw
from app.models import get_user_by_telegram_id, list_moderators
from app.menu_utils import get_menu_markup_for_user
from app.keyboards import (
    kb_support,
    kb_editor_orders_list,
    kb_editor_my_orders_list,
    kb_deals_list,
    kb_balance_menu,
    kb_balance_history,
    kb_about_menu,
    kb_nav_menu_help,
)
from app.profile_repo import get_editor_profile
from app.order_repo import list_open_orders, list_orders_for_editor, list_deals_for_client, list_deals_for_editor, get_user_balance, list_balance_transactions, withdraw_balance, set_user_withdrawal_verification
from app import texts

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

@router.callback_query(
    F.data.startswith(("client:", "editor:", "common:")) &
    ~F.data.in_(["client:profile", "editor:profile", "client:create_order", "client:my_orders", "common:settings"])
)
async def cb_menu(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        await call.answer(texts.tr(None, "Type /start", "Натисніть /start"), show_alert=True)
        return

    # ✅ "В меню"
    if call.data == "common:menu":
        await send_clean_from_call(
            call,
            state,
            texts.tr(user.language, "Menu:", "Меню:"),
            reply_markup=await get_menu_markup_for_user(user),
        )
        await call.answer()
        return

    # Заглушки / проверки:
    if call.data == "common:vip":
        await send_clean_from_call(
            call,
            state,
            texts.tr(user.language, "💎 VIP: coming soon.", "💎 VIP: скоро буде."),
            reply_markup=await get_menu_markup_for_user(user),
        )
    elif call.data == "common:support":
        admin_username = os.getenv("ADMIN_USERNAME", "").strip()
        if admin_username:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "🆘 Support: message the admin.", "🆘 Підтримка: напишіть адміну."),
                reply_markup=kb_support(admin_username, user.language),
            )
        else:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "🆘 Support: admin is not configured.", "🆘 Підтримка: адмін не налаштований."),
                reply_markup=await get_menu_markup_for_user(user),
            )
    elif call.data == "common:about":
        await send_clean_from_call(
            call,
            state,
            texts.tr(user.language, "About us", "Про нас"),
            reply_markup=kb_about_menu(user.language),
        )
    elif call.data == "common:about:ua":
        await send_clean_from_call(
            call,
            state,
            "🇺🇦 Українська\n\n" +
            "Чому саме ми\n\n" +
            "Ми створюємо не просто біржу, а безпечне середовище для роботи.\n" +
            "Оплата проходить через платформу, тому кошти захищені для обох сторін.\n" +
            "Система рейтингу сувора: кожне замовлення впливає на репутацію, що допомагає швидше знаходити надійних виконавців і замовників.\n" +
            "Також працює модерація — вона контролює порушення, спам і допомагає вирішувати спірні ситуації.\n\n" +
            "Як це працює\n\n" +
            "Замовник створює замовлення, вказує задачу, бюджет і терміни.\n" +
            "Монтажер відгукується та пропонує свої умови.\n" +
            "Після вибору виконавця угода переходить у безпечний режим: спілкування відбувається через платформу, а оплата резервується.\n" +
            "Після виконання роботи кошти переказуються виконавцю, а обидві сторони залишають відгук.",
            reply_markup=kb_nav_menu_help(back="common:menu", lang=user.language),
        )
    elif call.data == "common:about:en":
        await send_clean_from_call(
            call,
            state,
            "🇬🇧 English\n\n" +
            "Why choose us\n\n" +
            "We’re not just a marketplace — we’re a secure work environment.\n" +
            "Payments are handled through the platform, so funds are protected for both sides.\n" +
            "Our rating system is strict: every order affects reputation, helping users find reliable clients and editors faster.\n" +
            "We also have active moderation to handle violations, spam, and disputes.\n\n" +
            "How it works\n\n" +
            "A client creates an order with task details, budget, and deadline.\n" +
            "An editor applies and offers their terms.\n" +
            "Once selected, the deal moves into a secure mode: communication stays on the platform and payment is reserved.\n" +
            "After the work is completed and approved, funds are released to the editor, and both sides leave a review.",
            reply_markup=kb_nav_menu_help(back="common:menu", lang=user.language),
        )
    elif call.data == "editor:find_orders":
        p = await get_editor_profile(user.id)
        if not p or p.get("verification_status") != "verified":
            await call.answer(texts.tr(user.language, "⛔ Please verify first.", "⛔ Спочатку пройдіть верифікацію."), show_alert=True)
            return
        orders = await list_open_orders(limit=10)
        if not orders:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "🔎 No available orders yet.", "🔎 Доступних замовлень поки немає."),
                reply_markup=await get_menu_markup_for_user(user),
            )
        else:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "🔎 Available orders:", "🔎 Доступні замовлення:"),
                reply_markup=kb_editor_orders_list(orders, user.language),
            )
    elif call.data == "editor:my_proposals":
        orders = await list_orders_for_editor(user.id, limit=10)
        if not orders:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "📬 No proposals yet.", "📬 Відгуків поки немає."),
                reply_markup=await get_menu_markup_for_user(user),
            )
        else:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "📬 My proposals:", "📬 Мої відгуки:"),
                reply_markup=kb_editor_my_orders_list(orders, user.language),
            )
    elif call.data == "editor:my_deals":
        orders = await list_deals_for_editor(user.id, limit=10)
        if not orders:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "No active deals yet.", "Активних угод поки немає."),
                reply_markup=await get_menu_markup_for_user(user),
            )
        else:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "My deals:", "Мої угоди:"),
                reply_markup=kb_deals_list(orders, user.language),
            )
    elif call.data == "client:my_deals":
        orders = await list_deals_for_client(user.id, limit=10)
        if not orders:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "No active deals yet.", "Активних угод поки немає."),
                reply_markup=await get_menu_markup_for_user(user),
            )
        else:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "My deals:", "Мої угоди:"),
                reply_markup=kb_deals_list(orders, user.language),
            )

    elif call.data == "common:balance":
        balance_data = await get_user_balance(user.id)
        transactions = await list_balance_transactions(user.id, limit=5)
        await send_clean_from_call(
            call,
            state,
            texts.tr(user.language, "💰 Your balance:", "💰 Ваш баланс:"),
            reply_markup=kb_balance_menu(
                balance_data["virtual_balance_minor"],
                balance_data["total_earned_minor"],
                balance_data["verified_for_withdrawal"],
                user.language
            ),
        )

    elif call.data == "balance:history":
        transactions = await list_balance_transactions(user.id, limit=20)
        if not transactions:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "No transactions yet.", "Транзакцій поки немає."),
                reply_markup=kb_balance_menu(
                    (await get_user_balance(user.id))["virtual_balance_minor"],
                    (await get_user_balance(user.id))["total_earned_minor"],
                    (await get_user_balance(user.id))["verified_for_withdrawal"],
                    user.language
                ),
            )
        else:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "Transaction history:", "Історія транзакцій:"),
                reply_markup=kb_balance_history(transactions, user.language),
            )

    elif call.data == "balance:withdraw":
        balance_data = await get_user_balance(user.id)
        if not balance_data["verified_for_withdrawal"]:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "Withdrawal requires moderator verification. Request verification first.", "Вивід коштів вимагає верифікації модератора. Спочатку запросіть верифікацію."),
                reply_markup=kb_balance_menu(
                    balance_data["virtual_balance_minor"],
                    balance_data["total_earned_minor"],
                    balance_data["verified_for_withdrawal"],
                    user.language
                ),
            )
        elif balance_data["virtual_balance_minor"] <= 0:
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, "Insufficient balance for withdrawal.", "Недостатньо коштів для виводу."),
                reply_markup=kb_balance_menu(
                    balance_data["virtual_balance_minor"],
                    balance_data["total_earned_minor"],
                    balance_data["verified_for_withdrawal"],
                    user.language
                ),
            )
        else:
            await state.clear()
            await state.set_state(BalanceWithdraw.waiting_amount)
            await send_clean_from_call(
                call,
                state,
                texts.tr(user.language, f"Enter withdrawal amount (max: ${balance_data['virtual_balance_minor'] / 100:.2f}):", f"Введіть суму для виводу (макс: ${balance_data['virtual_balance_minor'] / 100:.2f}):"),
                reply_markup=None
            )

    elif call.data == "balance:verify_request":
        # Send verification request to moderators
        moderators = await list_moderators()
        for mod in moderators:
            await call.bot.send_message(
                mod.telegram_id,
                f"Verification request from user {user.display_name or user.username} (ID: {user.id}) for balance withdrawal."
            )
        await send_clean_from_call(
            call,
            state,
            texts.tr(user.language, "Verification request sent to moderators.", "Запит на верифікацію надіслано модераторам."),
            reply_markup=await get_menu_markup_for_user(user)
        )

    elif call.data == "balance:back":
        await send_clean_from_call(
            call,
            state,
            texts.tr(user.language, "Main menu:", "Головне меню:"),
            reply_markup=await get_menu_markup_for_user(user),
        )

    else:
        await send_clean_from_call(
            call,
            state,
            texts.tr(user.language, f"⏳ In development: {call.data}", f"⏳ Розділ у розробці: {call.data}"),
            reply_markup=await get_menu_markup_for_user(user),
        )

    await call.answer()

# ---------- Balance withdrawal handlers ----------

@router.message(BalanceWithdraw.waiting_amount)
async def balance_withdraw_amount(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await state.clear()
        return

    try:
        amount = float((message.text or "").strip())
        if amount <= 0:
            raise ValueError()
        amount_minor = int(amount * 100)
    except ValueError:
        await message.answer(texts.tr(user.language, "Please enter a valid amount.", "Будь ласка, введіть коректну суму."))
        return

    balance_data = await get_user_balance(user.id)
    if amount_minor > balance_data["virtual_balance_minor"]:
        await message.answer(texts.tr(user.language, "Insufficient balance.", "Недостатньо коштів."))
        await state.clear()
        return

    await state.update_data(withdraw_amount_minor=amount_minor)
    await state.set_state(BalanceWithdraw.waiting_description)

    await message.answer(
        texts.tr(user.language, "Enter description/payment details for withdrawal:", "Введіть опис/платіжні дані для виводу:"),
        reply_markup=None
    )

@router.message(BalanceWithdraw.waiting_description)
async def balance_withdraw_description(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await state.clear()
        return

    description = (message.text or "").strip()
    if not description:
        await message.answer(texts.tr(user.language, "Please enter description.", "Будь ласка, введіть опис."))
        return

    data = await state.get_data()
    amount_minor = data.get("withdraw_amount_minor")

    if not amount_minor:
        await state.clear()
        await message.answer(texts.tr(user.language, "Session expired. Please try again.", "Сесія закінчилася. Спробуйте ще раз."))
        return

    # Process withdrawal
    ok = await withdraw_balance(user.id, amount_minor, description)
    if not ok:
        await state.clear()
        await message.answer(texts.tr(user.language, "Withdrawal failed.", "Вивід коштів не вдалося."))
        return

    # Notify moderators
    moderators = await list_moderators()
    for mod in moderators:
        await message.bot.send_message(
            mod.telegram_id,
            f"Withdrawal request: User {user.display_name or user.username} (ID: {user.id}) requested withdrawal of ${amount_minor / 100:.2f}\nDetails: {description}"
        )

    await state.clear()
    await message.answer(
        texts.tr(user.language, "✅ Withdrawal request submitted. Moderators will process it.", "✅ Запит на вивід коштів подано. Модератори оброблять його."),
        reply_markup=await get_menu_markup_for_user(user)
    )
