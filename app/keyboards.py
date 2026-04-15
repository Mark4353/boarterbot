from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app import texts

def _lang_label(label_key: str, lang: str | None) -> str:
    return texts.t(label_key, lang)

def _tr(lang: str | None, en: str, ua: str) -> str:
    return texts.tr(lang, en, ua)

def kb_choose_role(lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    lng = texts.normalize_lang(lang)
    b.button(text=_lang_label("btn_role_client", lng), callback_data=f"role:client:{lng}")
    b.button(text=_lang_label("btn_role_editor", lng), callback_data=f"role:editor:{lng}")
    b.adjust(2)
    return b.as_markup()

def kb_nav(back: str | None = None, cancel: str = "reg:cancel", lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if back:
        b.button(text=_tr(lang, "⬅️ Back", "⬅️ Назад"), callback_data=back)
    b.button(text=_tr(lang, "❌ Cancel", "❌ Скасувати"), callback_data=cancel)
    b.adjust(2)
    return b.as_markup()

def kb_nav_portfolio_none(cancel: str = "reg:cancel", lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "No portfolio", "Без портфоліо"), callback_data="reg:portfolio:none")
    b.button(text=_tr(lang, "Cancel", "Скасувати"), callback_data=cancel)
    b.adjust(2)
    return b.as_markup()

def kb_skill_level(lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "Beginner", "Початківець"), callback_data="reg:skill_level:beginner")
    b.button(text=_tr(lang, "Intermediate", "Середній"), callback_data="reg:skill_level:intermediate")
    b.button(text=_tr(lang, "Professional", "Професійний"), callback_data="reg:skill_level:professional")
    b.button(text=_tr(lang, "Expert", "Експерт"), callback_data="reg:skill_level:expert")
    b.adjust(2)
    return b.as_markup()


def kb_nav_menu_help(
    back: str | None = None,
    menu: str = "common:menu",
    help_: str = "common:support",
    lang: str | None = None,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if back:
        b.button(text=_tr(lang, "Back", "Назад"), callback_data=back)
    b.button(text=_tr(lang, "Menu", "Меню"), callback_data=menu)
    b.button(text=_tr(lang, "Support", "Підтримка"), callback_data=help_)
    b.adjust(3)
    return b.as_markup()


def kb_about_menu(lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    lng = texts.normalize_lang(lang)
    b.button(text=_tr(lng, "🇺🇦 Ukrainian", "🇺🇦 Українська"), callback_data="common:about:ua")
    b.button(text=_tr(lng, "🇬🇧 English", "🇬🇧 English"), callback_data="common:about:en")
    b.button(text=_tr(lng, "Menu", "Меню"), callback_data="common:menu")
    b.adjust(1, 1, 1)
    return b.as_markup()


def kb_main_menu(role: str, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    lng = texts.normalize_lang(lang)

    if role == "client":
        b.button(text=_tr(lng, "➕ Create order", "➕ Створити замовлення"), callback_data="client:create_order")
        b.button(text=_tr(lng, "⬅️ Orders list", "⬅️ До списку"), callback_data="client:my_orders")
        b.button(text=_tr(lng, "💼 My deals", "💼 Мої угоди"), callback_data="client:my_deals")
        b.button(text=_tr(lng, "👤 Profile", "👤 Профіль"), callback_data="client:profile")
        b.button(text=_tr(lng, "ℹ️ About us", "ℹ️ Про нас"), callback_data="common:about")
        b.button(text=_lang_label("btn_settings", lng), callback_data="common:settings")
        b.button(text=_tr(lng, "💳 Balance", "💳 Баланс"), callback_data="common:balance")
        b.button(text=_tr(lng, "🆘 Support", "🆘 Підтримка"), callback_data="common:support")
        b.adjust(2, 2, 2, 1)

    elif role == "editor":
        b.button(text=_tr(lng, "👤 Profile", "👤 Профіль"), callback_data="editor:profile")
        b.button(text=_tr(lng, "✅ Verify", "✅ Верифікація"), callback_data="verify:start")
        b.button(text=_tr(lng, "📬 My proposals", "📬 Мої відгуки"), callback_data="editor:my_proposals")
        b.button(text=_tr(lng, "💼 My deals", "💼 Мої угоди"), callback_data="editor:my_deals")
        b.button(text=_tr(lng, "ℹ️ About us", "ℹ️ Про нас"), callback_data="common:about")
        b.button(text=_lang_label("btn_settings", lng), callback_data="common:settings")
        b.button(text=_tr(lng, "💳 Balance", "💳 Баланс"), callback_data="common:balance")
        b.button(text=_tr(lng, "🆘 Support", "🆘 Підтримка"), callback_data="common:support")
        b.adjust(2, 2, 2, 1)

    else:
        return kb_moderation_menu(lng)

    return b.as_markup()

def kb_moderation_menu(lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    lng = texts.normalize_lang(lang)
    b.button(text=_tr(lng, "🆕 New verifications", "🆕 Нові верифікації"), callback_data="mod:verifications")
    b.button(text=_tr(lng, "⚠️ Disputes", "⚠️ Спори"), callback_data="mod:disputes")
    b.button(text=_tr(lng, "💼 Active deals", "💼 Активні угоди"), callback_data="mod:active_deals")
    b.button(text=_tr(lng, "💬 Messages on review", "💬 Повідомлення на перевірці"), callback_data="mod:held_messages")
    b.button(text=_tr(lng, "🔎 Search", "🔎 Пошук"), callback_data="mod:search")
    b.button(text=_tr(lng, "📊 Stats", "📊 Статистика"), callback_data="mod:stats")
    b.button(text=_tr(lng, "🚫 Users / sanctions", "🚫 Користувачі / санкції"), callback_data="mod:users")
    b.button(text=_lang_label("btn_settings", lng), callback_data="common:settings")
    b.button(text=_tr(lng, "🏠 Menu", "🏠 Меню"), callback_data="common:menu")
    b.adjust(2, 2, 2, 2)
    return b.as_markup()

def kb_with_moderation_button(markup: InlineKeyboardMarkup, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for row in markup.inline_keyboard:
        b.row(*row)
    b.row(InlineKeyboardButton(text=_tr(lang, "🛠️ Moderator tools", "🛠️ Інструменти модератора"), callback_data="mod:menu"))
    return b.as_markup()

def kb_editor_menu(is_verified: bool, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    lng = texts.normalize_lang(lang)
    b.button(text=_tr(lng, "👤 Profile", "👤 Профіль"), callback_data="editor:profile")
    if is_verified:
        b.button(text=_tr(lng, "⬅️ Orders list", "⬅️ До списку"), callback_data="editor:find_orders")
    else:
        b.button(text=_tr(lng, "✅ Verify", "✅ Верифікація"), callback_data="verify:start")
    b.button(text=_tr(lng, "📬 My proposals", "📬 Мої відгуки"), callback_data="editor:my_proposals")
    b.button(text=_tr(lng, "💼 My deals", "💼 Мої угоди"), callback_data="editor:my_deals")
    b.button(text=_tr(lng, "ℹ️ About us", "ℹ️ Про нас"), callback_data="common:about")
    b.button(text=_lang_label("btn_settings", lng), callback_data="common:settings")
    b.button(text=_tr(lng, "💳 Balance", "💳 Баланс"), callback_data="common:balance")
    b.button(text=_tr(lng, "🆘 Support", "🆘 Підтримка"), callback_data="common:support")
    b.adjust(2, 2, 2, 1)
    return b.as_markup()

def kb_profile(role: str, verification_status: str | None = None, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    lng = texts.normalize_lang(lang)

    if role == "editor" and verification_status != "verified":
        b.button(text=_tr(lng, "✅ Verify", "✅ Верифікація"), callback_data="verify:start")

    b.button(text=_tr(lng, "🔁 Change role", "🔁 Змінити роль"), callback_data="profile:change_role")
    b.button(text=_lang_label("btn_settings", lng), callback_data="common:settings")
    b.button(text=_tr(lng, "🏠 Menu", "🏠 Меню"), callback_data="common:menu")
    b.adjust(1, 1, 1)
    return b.as_markup()

def kb_change_role_confirm(lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "I am a client", "Я замовник"), callback_data="profile:set_role:client")
    b.button(text=_tr(lang, "I am an editor", "Я монтажер"), callback_data="profile:set_role:editor")
    b.button(text=_tr(lang, "⬅️ Back", "⬅️ Назад"), callback_data="profile:back")
    b.adjust(2, 1)
    return b.as_markup()

def kb_verify_admin(editor_user_id: int, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "✅ Approve", "✅ Підтвердити"), callback_data=f"verify:approve:{editor_user_id}")
    b.button(text=_tr(lang, "❌ Reject", "❌ Відхилити"), callback_data=f"verify:reject:{editor_user_id}")
    b.button(text=_tr(lang, "✉️ Message", "✉️ Написати"), callback_data=f"verify:msg:{editor_user_id}")
    b.adjust(2, 1)
    return b.as_markup()

def kb_mod_verification_controls(user_id: int, offset: int, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "? Approve", "? ???????????"), callback_data=f"mod:verifications:approve:{user_id}:{offset}")
    b.button(text=_tr(lang, "? Reject", "? ?????????"), callback_data=f"mod:verifications:reject:{user_id}:{offset}")
    b.button(text=_tr(lang, "?? Chat", "?? ???"), callback_data=f"mod:verifications:chat:{user_id}")
    b.button(text=_tr(lang, "?? Back", "?? ?????"), callback_data="common:menu")
    b.button(text=_tr(lang, "?? Next", "?? ?????????"), callback_data=f"mod:verifications:page:{offset + 1}")
    b.adjust(2, 1, 2)
    return b.as_markup()



def kb_mod_held_controls(message_id: int, offset: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Approve", callback_data=f"mod:held_messages:approve:{message_id}:{offset}")
    b.button(text="❌ Reject", callback_data=f"mod:held_messages:reject:{message_id}:{offset}")
    b.button(text="🚫 Ban user", callback_data=f"mod:held_messages:ban:{message_id}:{offset}")
    b.button(text="✉️ Написать", callback_data=f"mod:held_messages:msg:{message_id}")
    b.button(text="⬅️ Назад", callback_data="common:menu")
    b.button(text="▶️ Следующий", callback_data=f"mod:held_messages:page:{offset + 1}")
    b.adjust(2, 2, 2)
    return b.as_markup()

def kb_mod_dispute_controls(deal_id: int, offset: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Выплатить исполнителю", callback_data=f"mod:disputes:pay:{deal_id}:{offset}")
    b.button(text="↩️ Вернуть заказчику", callback_data=f"mod:disputes:refund:{deal_id}:{offset}")
    b.button(text="✉️ Написать", callback_data=f"mod:disputes:msg:{deal_id}")
    b.button(text="⬅️ Назад", callback_data="common:menu")
    b.button(text="▶️ Следующий", callback_data=f"mod:disputes:page:{offset + 1}")
    b.adjust(1, 1, 1, 2)
    return b.as_markup()

def kb_mod_user_controls(user_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⚠️ Warning", callback_data=f"mod:user:warn:{user_id}")
    b.button(text="🚫 Ban", callback_data=f"mod:user:ban:{user_id}")
    b.button(text="✉️ Написать", callback_data=f"mod:user:msg:{user_id}")
    b.button(text="⬅️ Назад", callback_data="common:menu")
    b.adjust(2, 1, 1)
    return b.as_markup()

def kb_edit_editor_menu(lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "Change name", "Змінити ім'я"), callback_data="edit:editor:name")
    b.button(text=_tr(lang, "Change skills", "Змінити навички"), callback_data="edit:editor:skills")
    b.button(text=_tr(lang, "Change price", "Змінити ціну"), callback_data="edit:editor:price")
    b.button(text=_tr(lang, "Change portfolio", "Змінити портфоліо"), callback_data="edit:editor:portfolio")
    b.button(text=_tr(lang, "Back to profile", "До профілю"), callback_data="editor:profile")
    b.button(text=_tr(lang, "Menu", "Меню"), callback_data="common:menu")
    b.adjust(1)
    return b.as_markup()

def kb_edit_client_menu(lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "Change name", "Змінити ім'я"), callback_data="edit:client:name")
    b.button(text=_tr(lang, "Back to profile", "До профілю"), callback_data="client:profile")
    b.button(text=_tr(lang, "Menu", "Меню"), callback_data="common:menu")
    b.adjust(1)
    return b.as_markup()

def kb_language_start() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=texts.t("btn_lang_en", "en"), callback_data="lang:set:en")
    b.button(text=texts.t("btn_lang_uk", "ua"), callback_data="lang:set:ua")
    b.adjust(2)
    return b.as_markup()

def kb_settings_menu(role: str, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    lng = texts.normalize_lang(lang)
    has_edit = role in {"editor", "client"}
    if has_edit:
        target = "edit:editor_menu" if role == "editor" else "edit:client_menu"
        b.button(text=_lang_label("btn_edit_profile", lng), callback_data=target)
    b.button(
        text=_lang_label("btn_lang_en", lng) + (" ✅" if lng == "en" else ""),
        callback_data="lang:set:en",
    )
    b.button(
        text=_lang_label("btn_lang_uk", lng) + (" ✅" if lng == "ua" else ""),
        callback_data="lang:set:ua",
    )
    b.button(text=_lang_label("btn_menu", lng), callback_data="common:menu")
    sizes = [1, 2, 1] if has_edit else [2, 1]
    b.adjust(*sizes)
    return b.as_markup()

def kb_orders_list(orders: list[dict], lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for o in orders:
        title = (o.get("title") or "-").strip()
        if len(title) > 24:
            title = title[:21] + "..."
        b.button(text=f"#{o['id']} {title}", callback_data=f"order:view:{o['id']}")
    b.button(text=_tr(lang, "Menu", "Меню"), callback_data="common:menu")
    b.button(text=_tr(lang, "Support", "Підтримка"), callback_data="common:support")
    sizes = [1] * len(orders)
    sizes.append(2)
    b.adjust(*sizes)
    return b.as_markup()

def kb_order_detail(order_id: int, allow_edit: bool = False, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if allow_edit:
        b.button(text=_tr(lang, "Edit", "Редагувати"), callback_data=f"order:edit:{order_id}")
    b.button(text=_tr(lang, "Back to list", "До списку"), callback_data="client:my_orders")
    b.button(text=_tr(lang, "Menu", "Меню"), callback_data="common:menu")
    b.button(text=_tr(lang, "Support", "Підтримка"), callback_data="common:support")
    if allow_edit:
        b.adjust(1, 1, 2)
    else:
        b.adjust(1, 2)
    return b.as_markup()

def kb_support(admin_username: str, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    username = admin_username.lstrip("@")
    b.button(text=_tr(lang, "Message admin", "Написати адміну"), url=f"https://t.me/{username}")
    b.button(text=_tr(lang, "Menu", "Меню"), callback_data="common:menu")
    b.adjust(1, 1)
    return b.as_markup()

def kb_editor_orders_list(orders: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for o in orders:
        title = (o.get('title') or '-').strip()
        if len(title) > 24:
            title = title[:21] + '...'
        b.button(text=f"📄 Детали #{o['id']} {title}", callback_data=f"order:details:{o['id']}")
    b.button(text="🏠 Меню", callback_data="common:menu")
    b.button(text="🆘 Поддержка", callback_data="common:support")
    sizes = [1] * len(orders)
    sizes.append(2)
    b.adjust(*sizes)
    return b.as_markup()

def kb_editor_my_orders_list(orders: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for o in orders:
        title = (o.get("title") or "-").strip()
        if len(title) > 24:
            title = title[:21] + "..."
        b.button(text=f"📌 #{o['id']} {title}", callback_data=f"order:menu:{o['id']}")
    b.button(text="🏠 Меню", callback_data="common:menu")
    b.button(text="🆘 Поддержка", callback_data="common:support")
    sizes = [1] * len(orders)
    sizes.append(2)
    b.adjust(*sizes)
    return b.as_markup()

def kb_editor_order_detail(order_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💬 Начать чат", callback_data=f"order:chat:{order_id}")
    b.button(text="💰 Предложить цену", callback_data=f"order:proposal:{order_id}")
    b.button(text="⬅️ К списку", callback_data="editor:find_orders")
    b.button(text="🏠 Меню", callback_data="common:menu")
    b.button(text="🆘 Поддержка", callback_data="common:support")
    b.adjust(2, 1, 2)
    return b.as_markup()

def kb_deal_menu(order_id: int, lang: str | None = None, user_role: str = None, order_status: str = None, final_video_sent: bool = False, revision_requested: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "Chat", "Чат"), callback_data=f"deal:chat:{order_id}")

    if user_role == "editor" and order_status == "accepted":
        b.button(text=_tr(lang, "Complete order", "Завершити замовлення"), callback_data=f"order:complete:menu:{order_id}")
    elif user_role == "client" and order_status == "accepted" and final_video_sent:
        if revision_requested:
            b.button(text=_tr(lang, "Request revisions", "Запросити правки"), callback_data=f"order:revision:request:{order_id}")
        b.button(text=_tr(lang, "Confirm completion", "Підтвердити завершення"), callback_data=f"order:complete:confirm:{order_id}")

    b.button(text=_tr(lang, "Change", "Змінити"), callback_data=f"deal:change:{order_id}")
    b.button(text=_tr(lang, "Support", "Підтримка"), callback_data="common:support")
    b.adjust(2, 2)
    return b.as_markup()

def kb_deal_chat_menu(order_id: int, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "Start chat", "Почати чат"), callback_data=f"deal:chat:start:{order_id}")
    b.button(text=_tr(lang, "Dispute", "Спір"), callback_data=f"deal:dispute:{order_id}")
    b.button(text=_tr(lang, "To order menu", "До меню замовлення"), callback_data=f"deal:menu:{order_id}")
    b.adjust(1, 1, 1)
    return b.as_markup()

def kb_deal_chat_controls(order_id: int, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "Send link", "Надіслати посилання"), callback_data=f"deal:chat:link:{order_id}")
    b.button(text=_tr(lang, "Exit chat", "Вийти з чату"), callback_data=f"deal:chat:exit:{order_id}")
    b.button(text=_tr(lang, "Dispute", "Спір"), callback_data=f"deal:dispute:{order_id}")
    b.button(text=_tr(lang, "To order menu", "До меню замовлення"), callback_data=f"deal:menu:{order_id}")
    b.adjust(1, 1, 1, 1)
    return b.as_markup()

def kb_deal_chat_link_controls(order_id: int, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "Back to chat", "Назад до чату"), callback_data=f"deal:chat:start:{order_id}")
    b.button(text=_tr(lang, "To order menu", "До меню замовлення"), callback_data=f"deal:menu:{order_id}")
    b.adjust(1, 1)
    return b.as_markup()

def kb_mod_deal_menu(order_id: int, is_dispute: bool, payment_status: str | None = None, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "Read chat", "Читати чат"), callback_data=f"deal:chat:start:{order_id}")
    b.button(text=_tr(lang, "Chat with client", "Чат з замовником"), callback_data=f"mod:deal:chat:client:{order_id}")
    b.button(text=_tr(lang, "Chat with editor", "Чат з монтажером"), callback_data=f"mod:deal:chat:editor:{order_id}")
    b.button(text=_tr(lang, "Payment", "Оплата"), callback_data=f"mod:deal:payment:{order_id}")
    if is_dispute:
        b.button(text=_tr(lang, "Dispute", "Спір"), callback_data=f"deal:dispute:{order_id}")
    b.button(text=_tr(lang, "Back", "Назад"), callback_data="mod:active_deals")
    b.button(text=_tr(lang, "Menu", "Меню"), callback_data="common:menu")
    b.adjust(2, 2, 2)
    return b.as_markup()

def kb_mod_deal_payment_menu(order_id: int, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "Chat with client", "Чат з замовником"), callback_data=f"mod:deal:chat:client:{order_id}")
    b.button(text=_tr(lang, "Chat with editor", "Чат з монтажером"), callback_data=f"mod:deal:chat:editor:{order_id}")
    b.button(text=_tr(lang, "Join chat", "Увійти в чат"), callback_data=f"deal:chat:start:{order_id}")
    b.button(text=_tr(lang, "Refund to client", "Повернути оплату замовнику"), callback_data=f"mod:deal:refund:client:{order_id}")
    b.button(text=_tr(lang, "Partial refund to client", "???????? ?????????? ???????"), callback_data=f"mod:deal:refund:partial:{order_id}")
    b.button(text=_tr(lang, "Refund to editor", "Повернути оплату монтажеру"), callback_data=f"mod:deal:refund:editor:{order_id}")
    b.button(text=_tr(lang, "50/50 split", "50 на 50"), callback_data=f"mod:deal:split:{order_id}")
    b.button(text=_tr(lang, "Back", "Назад"), callback_data=f"mod:deal:menu:{order_id}")
    b.button(text=_tr(lang, "Menu", "Меню"), callback_data="common:menu")
    b.adjust(2, 2, 2, 2)
    return b.as_markup()

def kb_dispute_join(order_id: int, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "Join dispute", "Увійти в спір"), callback_data=f"deal:dispute:join:{order_id}")
    b.adjust(1)
    return b.as_markup()

def kb_dispute_controls(order_id: int, is_moderator: bool = False, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if is_moderator:
        b.button(text=_tr(lang, "Close dispute", "Закрити спір"), callback_data=f"deal:dispute:close:{order_id}")
    else:
        b.button(text=_tr(lang, "Agree to close dispute", "Згоден закрити спір"), callback_data=f"deal:dispute:agree:{order_id}")
    b.button(text=_tr(lang, "Exit", "Вийти"), callback_data=f"deal:dispute:exit:{order_id}")
    b.button(text=_tr(lang, "To order menu", "До меню замовлення"), callback_data=f"deal:menu:{order_id}")
    b.adjust(1, 1, 1)
    return b.as_markup()

def kb_proposal_actions(
    order_id: int,
    editor_id: int,
    proposal_price_minor: int | None = None,
    lang: str | None = None,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    price_part = f":{int(proposal_price_minor)}" if proposal_price_minor is not None else ""
    b.button(text=_tr(lang, "Start chat", "Почати чат"), callback_data=f"proposal:chat:{order_id}:{editor_id}")
    b.button(text=_tr(lang, "Accept", "Прийняти"), callback_data=f"proposal:accept:{order_id}:{editor_id}{price_part}")
    b.button(text=_tr(lang, "Reject", "Відхилити"), callback_data=f"proposal:reject:{order_id}:{editor_id}")
    b.adjust(1, 1, 1)
    return b.as_markup()

# ---------- Balance menu ----------

def kb_balance_menu(balance_minor: int, total_earned_minor: int, verified: bool, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    balance_text = f"{balance_minor / 100:.2f} USD"
    earned_text = f"{total_earned_minor / 100:.2f} USD"

    b.button(text=_tr(lang, f"💰 Balance: {balance_text}", f"💰 Баланс: {balance_text}"), callback_data="balance:info")
    b.button(text=_tr(lang, f"📈 Total earned: {earned_text}", f"📈 Загалом зароблено: {earned_text}"), callback_data="balance:info")

    if verified:
        b.button(text=_tr(lang, "💸 Withdraw funds", "💸 Вивести кошти"), callback_data="balance:withdraw")
    else:
        b.button(text=_tr(lang, "🔒 Withdrawal (needs verification)", "🔒 Вивід (потрібна верифікація)"), callback_data="balance:verify_request")

    b.button(text=_tr(lang, "📋 Transaction history", "📋 Історія транзакцій"), callback_data="balance:history")
    b.button(text=_tr(lang, "⬅️ Back", "⬅️ Назад"), callback_data="balance:back")
    b.adjust(1, 1, 1, 1)
    return b.as_markup()

def kb_balance_history(transactions: list[dict], lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    for tx in transactions[:5]:  # Show last 5 transactions
        amount = tx["amount_minor"] / 100
        tx_type = tx["transaction_type"]
        date = tx["created_at"].strftime("%d.%m.%Y")
        desc = tx.get("description", "")

        if tx_type == "earned":
            icon = "💰"
            text = f"{icon} +{amount:.2f} USD - {desc}"
        elif tx_type == "withdrawn":
            icon = "💸"
            text = f"{icon} -{abs(amount):.2f} USD - {desc}"
        else:
            icon = "🔄"
            text = f"{icon} {amount:.2f} USD - {desc}"

        b.button(text=text, callback_data=f"balance:tx_detail:{tx['id']}")

    b.button(text=_tr(lang, "⬅️ Back to balance", "⬅️ Назад до балансу"), callback_data="balance:back")
    b.adjust(1)
    return b.as_markup()

# ---------- Revision request menu ----------

def kb_revision_request_menu(order_id: int, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "📝 Request revision", "📝 Запросити правки"), callback_data=f"order:revision:request:{order_id}")
    b.button(text=_tr(lang, "⬅️ Back", "⬅️ Назад"), callback_data=f"order:menu:{order_id}")
    b.adjust(1, 1)
    return b.as_markup()

def kb_revision_response_menu(order_id: int, revision_description: str, proposed_price_minor: int, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    price_text = f"{proposed_price_minor / 100:.2f} USD"

    b.button(text=_tr(lang, f"✅ Accept ({price_text})", f"✅ Прийняти ({price_text})"), callback_data=f"revision:accept:{order_id}")
    b.button(text=_tr(lang, "💰 Propose different price", "💰 Запропонувати іншу ціну"), callback_data=f"revision:counter:{order_id}")
    b.button(text=_tr(lang, "❌ Reject revision", "❌ Відхилити правки"), callback_data=f"revision:reject:{order_id}")
    b.button(text=_tr(lang, "💬 Discuss with client", "💬 Обговорити з замовником"), callback_data=f"revision:chat:{order_id}")
    b.adjust(1, 1, 1, 1)
    return b.as_markup()

# ---------- Order completion menu ----------

def kb_order_completion_menu(order_id: int, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "📤 Send final video", "📤 Надіслати фінальне відео"), callback_data=f"order:complete:send_video:{order_id}")
    b.button(text=_tr(lang, "⬅️ Back", "⬅️ Назад"), callback_data=f"order:menu:{order_id}")
    b.adjust(1, 1)
    return b.as_markup()

def kb_client_completion_menu(order_id: int, has_revisions: bool, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    if has_revisions:
        b.button(text=_tr(lang, "📝 Request revisions", "📝 Запросити правки"), callback_data=f"order:revision:request:{order_id}")
        b.button(text=_tr(lang, "✅ Confirm completion", "✅ Підтвердити завершення"), callback_data=f"order:complete:confirm:{order_id}")
    else:
        b.button(text=_tr(lang, "✅ Confirm completion", "✅ Підтвердити завершення"), callback_data=f"order:complete:confirm:{order_id}")

    b.button(text=_tr(lang, "💬 Chat with editor", "💬 Чат з монтажером"), callback_data=f"order:chat:{order_id}")
    b.button(text=_tr(lang, "⬅️ Back", "⬅️ Назад"), callback_data=f"order:menu:{order_id}")
    b.adjust(1, 1, 1)
    return b.as_markup()

def kb_deals_list(orders: list[dict], lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for o in orders:
        title = (o.get("title") or "-").strip()
        if len(title) > 24:
            title = title[:21] + "..."
        status = (o.get("status") or "").strip()
        label = f"#{o['id']} {title}"
        if status:
            label = f"{label} ({status})"
        b.button(text=label, callback_data=f"deal:menu:{o['id']}")
    b.button(text=_tr(lang, "Menu", "Меню"), callback_data="common:menu")
    b.button(text=_tr(lang, "Support", "Підтримка"), callback_data="common:support")
    sizes = [1] * len(orders)
    sizes.append(2)
    b.adjust(*sizes)
    return b.as_markup()

def kb_deadline_quick(back: str, cancel: str, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "24 hours", "24 години"), callback_data="deadline:hours:24")
    b.button(text=_tr(lang, "3 days", "3 дні"), callback_data="deadline:days:3")
    b.button(text=_tr(lang, "7 days", "7 днів"), callback_data="deadline:days:7")
    b.button(text=_tr(lang, "14 days", "14 днів"), callback_data="deadline:days:14")
    b.button(text=_tr(lang, "Custom date", "Свій термін"), callback_data="deadline:custom")
    b.button(text=_tr(lang, "Back", "Назад"), callback_data=back)
    b.button(text=_tr(lang, "Cancel", "Скасувати"), callback_data=cancel)
    b.adjust(2, 2, 1, 2)
    return b.as_markup()



def kb_verify_chat_reply(moderator_user_id: int, lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "?? Reply", "?? ??????????"), callback_data=f"verify:chat:reply:{moderator_user_id}")
    b.adjust(1)
    return b.as_markup()



def kb_verify_chat_controls(lang: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=_tr(lang, "?? Exit", "?? ?????"), callback_data="verify:chat:exit")
    b.adjust(1)
    return b.as_markup()

