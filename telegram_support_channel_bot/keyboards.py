from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="❓ Задать вопрос",
                callback_data="ask_question"
            ),
            InlineKeyboardButton(
                text="📢 Наш канал",
                url="https://t.me/your_channel"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 FAQ",
                callback_data="faq"
            ),
            InlineKeyboardButton(
                text="💡 Предложить идею",
                callback_data="suggest_idea"
            )
        ],
        [
            InlineKeyboardButton(
                text="🐛 Сообщить об ошибке",
                callback_data="report_bug"
            )
        ]
    ]

    if is_admin:
        buttons.append([
            InlineKeyboardButton(
                text="⚙️ Админ-панель",
                callback_data="admin_panel"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def faq_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="📌 Как подписаться?",
                callback_data="faq_subscribe"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔔 Как включить уведомления?",
                callback_data="faq_notifications"
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 Как предложить пост?",
                callback_data="faq_post"
            )
        ],
        [
            InlineKeyboardButton(
                text="💰 Реклама на канале",
                callback_data="faq_ads"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cancel_action() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="main_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_answer(user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="✉️ Ответить пользователю",
                callback_data=f"answer_{user_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_panel() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="📊 Статистика обращений",
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="👥 Список пользователей",
                callback_data="users_list_0"
            )
        ],
        [
            InlineKeyboardButton(
                text="📣 Сделать рассылку",
                callback_data="admin_broadcast"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_stats_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data="admin_stats_refresh"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад в панель",
                callback_data="admin_panel"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def broadcast_confirm() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Отправить всем",
                callback_data="broadcast_confirm"
            ),
            InlineKeyboardButton(
                text="✏️ Изменить",
                callback_data="broadcast_edit"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="admin_panel"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cancel_broadcast() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="❌ Отменить рассылку",
                callback_data="admin_panel"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def users_list_nav(
    current_page: int,
    total_pages: int
) -> InlineKeyboardMarkup:
    buttons = []

    nav_row = []

    if current_page > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"users_list_{current_page - 1}"
            )
        )

    nav_row.append(
        InlineKeyboardButton(
            text=f"📄 {current_page + 1} / {total_pages}",
            callback_data="users_page_info"
        )
    )

    if current_page < total_pages - 1:
        nav_row.append(
            InlineKeyboardButton(
                text="Вперёд ▶️",
                callback_data=f"users_list_{current_page + 1}"
            )
        )

    buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=f"users_list_{current_page}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад в панель",
            callback_data="admin_panel"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
