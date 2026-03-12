from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def kb_choose_role() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Я заказчик", callback_data="role:client")
    b.button(text="Я монтажёр", callback_data="role:editor")
    b.adjust(2)
    return b.as_markup()

def kb_nav(back: str | None = None, cancel: str = "reg:cancel") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if back:
        b.button(text="⬅️ Назад", callback_data=back)
    b.button(text="❌ Отмена", callback_data=cancel)
    b.adjust(2)
    return b.as_markup()

def kb_nav_menu_help(
    back: str | None = None,
    menu: str = "common:menu",
    help_: str = "common:support",
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if back:
        b.button(text="⬅️ Назад", callback_data=back)
    b.button(text="🏠 Меню", callback_data=menu)
    b.button(text="🆘 Помощь", callback_data=help_)
    b.adjust(3)
    return b.as_markup()

def kb_main_menu(role: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    if role == "client":
        b.button(text="➕ Создать заказ", callback_data="client:create_order")
        b.button(text="📦 Мои заказы", callback_data="client:my_orders")
        b.button(text="💼 Мои сделки", callback_data="client:my_deals")
        b.button(text="👤 Профиль", callback_data="client:profile")
        b.button(text="💳 Баланс", callback_data="common:balance")
        b.button(text="🆘 Поддержка", callback_data="common:support")
        b.adjust(2, 2, 2)

    elif role == "editor":
        b.button(text="👤 Профиль", callback_data="editor:profile")
        b.button(text="✅ Пройти верификацию", callback_data="verify:start")
        b.button(text="📬 Мои отклики", callback_data="editor:my_proposals")
        b.button(text="💼 Мои сделки", callback_data="editor:my_deals")
        b.button(text="💳 Баланс", callback_data="common:balance")
        b.button(text="🆘 Поддержка", callback_data="common:support")
        b.adjust(2, 2, 2)

    else:
        b.button(text="🆕 Сообщения на проверке", callback_data="mod:held_messages")
        b.button(text="⚠️ Споры", callback_data="mod:disputes")
        b.button(text="📊 Статистика", callback_data="mod:stats")
        b.adjust(1)

    return b.as_markup()

def kb_editor_menu(is_verified: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="👤 Профиль", callback_data="editor:profile")
    if is_verified:
        b.button(text="🔎 Найти заказы", callback_data="editor:find_orders")
    else:
        b.button(text="✅ Пройти верификацию", callback_data="verify:start")
        b.button(text="🧪 Авто-верификация (тест)", callback_data="verify:auto")
    b.button(text="📬 Мои отклики", callback_data="editor:my_proposals")
    b.button(text="💼 Мои сделки", callback_data="editor:my_deals")
    b.button(text="💳 Баланс", callback_data="common:balance")
    b.button(text="🆘 Поддержка", callback_data="common:support")
    b.adjust(2, 2, 2)
    return b.as_markup()

def kb_profile(role: str, verification_status: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    if role == "editor":
        b.button(text="✏️ Изменить информацию", callback_data="edit:editor_menu")
        if verification_status != "verified":
            b.button(text="✅ Пройти верификацию", callback_data="verify:start")
    elif role == "client":
        b.button(text="✏️ Изменить информацию", callback_data="edit:client_menu")

    b.button(text="🔁 Сменить роль", callback_data="profile:change_role")
    b.button(text="⬅️ В меню", callback_data="common:menu")
    b.adjust(1)
    return b.as_markup()

def kb_change_role_confirm() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Я заказчик", callback_data="profile:set_role:client")
    b.button(text="Я монтажёр", callback_data="profile:set_role:editor")
    b.button(text="⬅️ Назад", callback_data="profile:back")
    b.adjust(2, 1)
    return b.as_markup()

def kb_verify_admin(editor_user_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Approve", callback_data=f"verify:approve:{editor_user_id}")
    b.button(text="❌ Reject", callback_data=f"verify:reject:{editor_user_id}")
    b.button(text="✉️ Написать", callback_data=f"verify:msg:{editor_user_id}")
    b.adjust(2, 1)
    return b.as_markup()

def kb_edit_editor_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="👤 Изменить имя", callback_data="edit:editor:name")
    b.button(text="🎬 Изменить специализации", callback_data="edit:editor:skills")
    b.button(text="💰 Изменить цену", callback_data="edit:editor:price")
    b.button(text="📁 Изменить портфолио", callback_data="edit:editor:portfolio")
    b.button(text="⬅️ В профиль", callback_data="editor:profile")
    b.button(text="🏠 В меню", callback_data="common:menu")
    b.adjust(1)
    return b.as_markup()

def kb_edit_client_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="👤 Изменить имя", callback_data="edit:client:name")
    b.button(text="⬅️ В профиль", callback_data="client:profile")
    b.button(text="🏠 В меню", callback_data="common:menu")
    b.adjust(1)
    return b.as_markup()

def kb_orders_list(orders: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for o in orders:
        title = (o.get("title") or "-").strip()
        if len(title) > 24:
            title = title[:21] + "..."
        b.button(text=f"#{o['id']} {title}", callback_data=f"order:view:{o['id']}")
    b.button(text="🏠 Меню", callback_data="common:menu")
    b.button(text="🆘 Помощь", callback_data="common:support")
    sizes = [1] * len(orders)
    sizes.append(2)
    b.adjust(*sizes)
    return b.as_markup()

def kb_order_detail(order_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ К списку", callback_data="client:my_orders")
    b.button(text="🏠 Меню", callback_data="common:menu")
    b.button(text="🆘 Помощь", callback_data="common:support")
    b.adjust(1, 2)
    return b.as_markup()

def kb_support(admin_username: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    username = admin_username.lstrip("@")
    b.button(text="✉️ Написать админу", url=f"https://t.me/{username}")
    b.button(text="🏠 В меню", callback_data="common:menu")
    b.adjust(1, 1)
    return b.as_markup()

def kb_editor_orders_list(orders: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for o in orders:
        title = (o.get("title") or "-").strip()
        if len(title) > 24:
            title = title[:21] + "..."
        b.button(text=f"✅ Принять #{o['id']} {title}", callback_data=f"order:accept:{o['id']}")
    b.button(text="🏠 Меню", callback_data="common:menu")
    b.button(text="🆘 Поддержка", callback_data="common:support")
    sizes = [1] * len(orders)
    sizes.append(2)
    b.adjust(*sizes)
    return b.as_markup()
