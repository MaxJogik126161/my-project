from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="❓ Задать вопрос", callback_data="ask_question"),
            InlineKeyboardButton(text="📢 Наш канал", url="https://t.me/your_channel")
        ],
        [
            InlineKeyboardButton(text="📋 FAQ", callback_data="faq"),
            InlineKeyboardButton(text="💡 Предложить идею", callback_data="suggest_idea")
        ],
        [
            InlineKeyboardButton(text="🐛 Сообщить об ошибке", callback_data="report_bug")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def faq_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📌 Как подписаться?", callback_data="faq_subscribe")],
        [InlineKeyboardButton(text="🔔 Как включить уведомления?", callback_data="faq_notifications")],
        [InlineKeyboardButton(text="📝 Как предложить пост?", callback_data="faq_post")],
        [InlineKeyboardButton(text="💰 Реклама на канале", callback_data="faq_ads")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cancel_action() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")
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
