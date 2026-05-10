import asyncio
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest

from keyboards import (
    main_menu,
    back_to_menu,
    faq_menu,
    cancel_action,
    admin_answer,
    admin_panel,
    admin_stats_menu,
    broadcast_confirm,
    cancel_broadcast,
    users_list_nav,
)
from config import ADMIN_ID, CHANNEL_ID
from stats import stats
from users import user_storage

logger = logging.getLogger(__name__)

router = Router()

PAGE_SIZE = 10

class UserStates(StatesGroup):
    waiting_question = State()
    waiting_idea = State()
    waiting_bug = State()
    waiting_admin_answer = State()
    waiting_broadcast = State()

FAQ_ANSWERS = {
    "faq_subscribe": (
        "📌 <b>Как подписаться на канал?</b>\n\n"
        "1. Нажмите на ссылку канала\n"
        "2. Нажмите кнопку <b>«Подписаться»</b>\n"
        "3. Готово! Теперь вы будете получать все новые посты 🎉"
    ),
    "faq_notifications": (
        "🔔 <b>Как включить уведомления?</b>\n\n"
        "1. Зайдите на страницу канала\n"
        "2. Нажмите на колокольчик 🔔\n"
        "3. Выберите <b>«Включить уведомления»</b>\n\n"
        "Теперь вы не пропустите ни одного поста!"
    ),
    "faq_post": (
        "📝 <b>Как предложить пост?</b>\n\n"
        "Вы можете предложить идею для поста через кнопку\n"
        "<b>«💡 Предложить идею»</b> в главном меню.\n\n"
        "Мы рассматриваем все предложения от подписчиков!"
    ),
    "faq_ads": (
        "💰 <b>Реклама на канале</b>\n\n"
        "Для размещения рекламы свяжитесь с администратором "
        "через кнопку <b>«❓ Задать вопрос»</b>\n\n"
        "Укажите в сообщении:\n"
        "• Тематику рекламы\n"
        "• Желаемые сроки\n"
        "• Контакт для связи"
    ),
}

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def build_users_page(page: int) -> str:
    total = user_storage.count()
    total_pages = user_storage.total_pages(PAGE_SIZE)
    users = user_storage.get_page(page, PAGE_SIZE)

    lines = [
        "👥 <b>Список пользователей</b>",
        "━━━━━━━━━━━━━━━━━━\n",
        f"📊 Всего пользователей: <b>{total}</b>\n",
    ]

    if not users:
        lines.append("😔 Пользователей пока нет")
        return "\n".join(lines)

    start_index = page * PAGE_SIZE
    for index, user in enumerate(users, start=start_index + 1):
        username_part = (
            f"@{user.username}"
            if user.username
            else "нет username"
        )
        lines.append(
            f"{index}. <a href='tg://user?id={user.user_id}'>"
            f"{user.full_name}</a>\n"
            f"     🆔 <code>{user.user_id}</code> | "
            f"📝 {username_part}"
        )

    lines.append(f"\n━━━━━━━━━━━━━━━━━━")
    lines.append(
        f"📄 Страница <b>{page + 1}</b> из <b>{total_pages}</b>"
    )

    return "\n".join(lines)

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

    user = message.from_user

    user_storage.add(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username
    )

    admin = is_admin(user.id)

    await message.answer(
        text=(
            f"👋 Привет, <b>{user.first_name}</b>!\n\n"
            f"Это бот поддержки канала <b>{CHANNEL_ID}</b>\n\n"
            "Я помогу тебе:\n"
            "❓ Задать вопрос администратору\n"
            "📋 Найти ответы в FAQ\n"
            "💡 Предложить идею для контента\n"
            "🐛 Сообщить об ошибке\n\n"
            "Выбери нужный раздел 👇"
        ),
        reply_markup=main_menu(is_admin=admin),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    await state.clear()
    admin = is_admin(callback.from_user.id)

    await callback.message.edit_text(
        text=(
            "🏠 <b>Главное меню</b>\n\n"
            "Выбери нужный раздел 👇"
        ),
        reply_markup=main_menu(is_admin=admin),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "ask_question")
async def callback_ask_question(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    await state.set_state(UserStates.waiting_question)
    await callback.message.edit_text(
        text=(
            "❓ <b>Задать вопрос</b>\n\n"
            "Напишите ваш вопрос в следующем сообщении.\n"
            "Администратор ответит вам в ближайшее время.\n\n"
            "<i>Нажмите «Отмена» чтобы вернуться в меню</i>"
        ),
        reply_markup=cancel_action(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.waiting_question)
async def process_question(
    message: Message,
    state: FSMContext,
    bot: Bot
) -> None:
    user = message.from_user

    user_storage.add(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username
    )

    stats.add_question()

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📨 <b>Новый вопрос от пользователя!</b>\n\n"
            f"👤 Пользователь: "
            f"<a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📝 Username: "
            f"@{user.username if user.username else 'нет'}\n\n"
            f"❓ <b>Вопрос:</b>\n{message.text}"
        ),
        reply_markup=admin_answer(user.id),
        parse_mode="HTML"
    )

    await state.clear()
    await message.answer(
        text=(
            "✅ <b>Вопрос отправлен!</b>\n\n"
            "Администратор ответит вам в ближайшее время.\n"
            "Спасибо за обращение! 🙏"
        ),
        reply_markup=back_to_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "suggest_idea")
async def callback_suggest_idea(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    await state.set_state(UserStates.waiting_idea)
    await callback.message.edit_text(
        text=(
            "💡 <b>Предложить идею</b>\n\n"
            "Опишите вашу идею для контента канала.\n"
            "Мы читаем каждое предложение!\n\n"
            "<i>Нажмите «Отмена» чтобы вернуться в меню</i>"
        ),
        reply_markup=cancel_action(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.waiting_idea)
async def process_idea(
    message: Message,
    state: FSMContext,
    bot: Bot
) -> None:
    user = message.from_user

    user_storage.add(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username
    )

    stats.add_idea()

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "💡 <b>Новая идея от пользователя!</b>\n\n"
            f"👤 Пользователь: "
            f"<a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📝 Username: "
            f"@{user.username if user.username else 'нет'}\n\n"
            f"💡 <b>Идея:</b>\n{message.text}"
        ),
        parse_mode="HTML"
    )

    await state.clear()
    await message.answer(
        text=(
            "✅ <b>Идея отправлена!</b>\n\n"
            "Спасибо за ваш вклад в развитие канала! 🎉\n"
            "Мы обязательно рассмотрим ваше предложение."
        ),
        reply_markup=back_to_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "report_bug")
async def callback_report_bug(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    await state.set_state(UserStates.waiting_bug)
    await callback.message.edit_text(
        text=(
            "🐛 <b>Сообщить об ошибке</b>\n\n"
            "Опишите проблему как можно подробнее:\n"
            "• Что произошло?\n"
            "• Когда это случилось?\n"
            "• Что вы ожидали увидеть?\n\n"
            "<i>Нажмите «Отмена» чтобы вернуться в меню</i>"
        ),
        reply_markup=cancel_action(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.waiting_bug)
async def process_bug(
    message: Message,
    state: FSMContext,
    bot: Bot
) -> None:
    user = message.from_user

    user_storage.add(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username
    )

    stats.add_bug()

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🐛 <b>Новый баг-репорт!</b>\n\n"
            f"👤 Пользователь: "
            f"<a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📝 Username: "
            f"@{user.username if user.username else 'нет'}\n\n"
            f"🐛 <b>Описание ошибки:</b>\n{message.text}"
        ),
        parse_mode="HTML"
    )

    await state.clear()
    await message.answer(
        text=(
            "✅ <b>Баг-репорт отправлен!</b>\n\n"
            "Спасибо что помогаете нам стать лучше! 🙏\n"
            "Мы разберёмся с проблемой."
        ),
        reply_markup=back_to_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "faq")
async def callback_faq(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        text=(
            "📋 <b>Часто задаваемые вопросы</b>\n\n"
            "Выберите интересующий вас вопрос 👇"
        ),
        reply_markup=faq_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.in_(FAQ_ANSWERS.keys()))
async def callback_faq_answer(callback: CallbackQuery) -> None:
    answer = FAQ_ANSWERS.get(callback.data)
    await callback.message.edit_text(
        text=answer,
        reply_markup=faq_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("answer_"))
async def callback_admin_answer(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа!", show_alert=True)
        return

    user_id = int(callback.data.split("_")[1])
    await state.update_data(reply_to_user=user_id)
    await state.set_state(UserStates.waiting_admin_answer)

    await callback.message.answer(
        text=(
            f"✉️ <b>Ответ пользователю</b> "
            f"<code>{user_id}</code>\n\n"
            "Напишите ответ в следующем сообщении:"
        ),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(
    UserStates.waiting_admin_answer,
    F.from_user.id == ADMIN_ID
)
async def process_admin_answer(
    message: Message,
    state: FSMContext,
    bot: Bot
) -> None:
    data = await state.get_data()
    user_id = data.get("reply_to_user")

    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                "📩 <b>Ответ от администратора канала</b>\n\n"
                f"{message.text}"
            ),
            parse_mode="HTML"
        )
        await state.clear()
        await message.answer(
            text="✅ <b>Ответ успешно отправлен пользователю!</b>",
            parse_mode="HTML"
        )
    except Exception as error:
        await message.answer(
            text=(
                f"❌ <b>Ошибка отправки:</b> "
                f"<code>{error}</code>"
            ),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "admin_panel")
async def callback_admin_panel(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа!", show_alert=True)
        return

    await callback.message.edit_text(
        text=(
            "⚙️ <b>Админ-панель</b>\n\n"
            f"👥 Пользователей в базе: "
            f"<b>{user_storage.count()}</b>\n\n"
            "Выберите нужный раздел 👇"
        ),
        reply_markup=admin_panel(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа!", show_alert=True)
        return

    await callback.message.edit_text(
        text=stats.format_stats(),
        reply_markup=admin_stats_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_stats_refresh")
async def callback_admin_stats_refresh(
    callback: CallbackQuery
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа!", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            text=stats.format_stats(),
            reply_markup=admin_stats_menu(),
            parse_mode="HTML"
        )
        await callback.answer("✅ Статистика обновлена!")
    except TelegramBadRequest as error:
        if "message is not modified" in str(error):
            await callback.answer(
                "📊 Статистика актуальна, новых обращений нет!"
            )
        else:
            raise

@router.callback_query(F.data.startswith("users_list_"))
async def callback_users_list(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа!", show_alert=True)
        return

    page = int(callback.data.split("_")[2])
    total_pages = user_storage.total_pages(PAGE_SIZE)

    if page < 0:
        page = 0
    if page >= total_pages:
        page = total_pages - 1

    try:
        await callback.message.edit_text(
            text=build_users_page(page),
            reply_markup=users_list_nav(page, total_pages),
            parse_mode="HTML"
        )
    except TelegramBadRequest as error:
        if "message is not modified" in str(error):
            await callback.answer("✅ Список актуален!")
        else:
            raise

    await callback.answer()

@router.callback_query(F.data == "users_page_info")
async def callback_users_page_info(callback: CallbackQuery) -> None:
    total = user_storage.count()
    total_pages = user_storage.total_pages(PAGE_SIZE)
    await callback.answer(
        f"👥 Всего: {total} пользователей | "
        f"📄 Страниц: {total_pages}",
        show_alert=True
    )

@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа!", show_alert=True)
        return

    total = user_storage.count()

    if total == 0:
        await callback.answer(
            "⚠️ Нет пользователей для рассылки!",
            show_alert=True
        )
        return

    await state.set_state(UserStates.waiting_broadcast)
    await callback.message.edit_text(
        text=(
            "📣 <b>Рассылка сообщений</b>\n\n"
            f"👥 Получателей: <b>{total}</b> пользователей\n\n"
            "Напишите сообщение для рассылки.\n"
            "Поддерживается <b>HTML</b> форматирование:\n"
            "<code>&lt;b&gt;жирный&lt;/b&gt;</code>\n"
            "<code>&lt;i&gt;курсив&lt;/i&gt;</code>\n"
            "<code>&lt;code&gt;код&lt;/code&gt;</code>\n\n"
            "<i>Нажмите «Отменить рассылку» чтобы вернуться</i>"
        ),
        reply_markup=cancel_broadcast(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(
    UserStates.waiting_broadcast,
    F.from_user.id == ADMIN_ID
)
async def process_broadcast_text(
    message: Message,
    state: FSMContext
) -> None:
    await state.update_data(broadcast_text=message.text)

    total = user_storage.count()

    await message.answer(
        text=(
            "👀 <b>Превью рассылки</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"{message.text}\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"📤 Будет отправлено: <b>{total}</b> пользователям\n\n"
            "Подтвердите отправку или измените текст 👇"
        ),
        reply_markup=broadcast_confirm(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "broadcast_edit")
async def callback_broadcast_edit(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа!", show_alert=True)
        return

    total = user_storage.count()
    await state.set_state(UserStates.waiting_broadcast)

    await callback.message.edit_text(
        text=(
            "✏️ <b>Изменить текст рассылки</b>\n\n"
            f"👥 Получателей: <b>{total}</b> пользователей\n\n"
            "Напишите новый текст для рассылки 👇"
        ),
        reply_markup=cancel_broadcast(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "broadcast_confirm")
async def callback_broadcast_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа!", show_alert=True)
        return

    data = await state.get_data()
    broadcast_text = data.get("broadcast_text")
    await state.clear()

    users = user_storage.all()
    total = len(users)

    success = 0
    failed = 0

    progress_message = await callback.message.edit_text(
        text=(
            "📤 <b>Рассылка запущена...</b>\n\n"
            f"⏳ Отправляем: 0 / {total}"
        ),
        parse_mode="HTML"
    )
    await callback.answer()

    for index, user in enumerate(users, start=1):
        if user.user_id == ADMIN_ID:
            total -= 1
            continue

        try:
            await bot.send_message(
                chat_id=user.user_id,
                text=(
                    "📢 <b>Сообщение от администратора канала</b>\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"
                    f"{broadcast_text}"
                ),
                parse_mode="HTML"
            )
            success += 1
        except TelegramBadRequest as error:
            logger.warning(
                "Broadcast failed for user %s: %s",
                user.user_id, error
            )
            failed += 1
        except Exception as error:
            logger.warning(
                "Broadcast failed for user %s: %s",
                user.user_id, error
            )
            failed += 1

        if index % 10 == 0:
            try:
                await progress_message.edit_text(
                    text=(
                        "📤 <b>Рассылка в процессе...</b>\n\n"
                        f"⏳ Отправляем: {index} / {total}"
                    ),
                    parse_mode="HTML"
                )
            except TelegramBadRequest:
                pass

        await asyncio.sleep(0.05)

    await progress_message.edit_text(
        text=(
            "✅ <b>Рассылка завершена!</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"📤 Всего получателей: <b>{total}</b>\n"
            f"✅ Успешно доставлено: <b>{success}</b>\n"
            f"❌ Не доставлено: <b>{failed}</b>"
        ),
        reply_markup=admin_panel(),
        parse_mode="HTML"
    )
