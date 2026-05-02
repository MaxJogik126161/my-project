from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart

from keyboards import (
    main_menu,
    back_to_menu,
    faq_menu,
    cancel_action,
    admin_answer
)
from config import ADMIN_ID, CHANNEL_ID

router = Router()

class UserStates(StatesGroup):
    waiting_question = State()
    waiting_idea = State()
    waiting_bug = State()
    waiting_admin_answer = State()

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

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_name = message.from_user.first_name
    await message.answer(
        text=(
            f"👋 Привет, <b>{user_name}</b>!\n\n"
            f"Это бот поддержки канала <b>{CHANNEL_ID}</b>\n\n"
            "Я помогу тебе:\n"
            "❓ Задать вопрос администратору\n"
            "📋 Найти ответы в FAQ\n"
            "💡 Предложить идею для контента\n"
            "🐛 Сообщить об ошибке\n\n"
            "Выбери нужный раздел 👇"
        ),
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        text=(
            "🏠 <b>Главное меню</b>\n\n"
            "Выбери нужный раздел 👇"
        ),
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "ask_question")
async def callback_ask_question(callback: CallbackQuery, state: FSMContext) -> None:
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
async def process_question(message: Message, state: FSMContext, bot: Bot) -> None:
    user = message.from_user
    question_text = message.text

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📨 <b>Новый вопрос от пользователя!</b>\n\n"
            f"👤 Пользователь: <a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📝 Username: @{user.username if user.username else 'нет'}\n\n"
            f"❓ <b>Вопрос:</b>\n{question_text}"
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
async def callback_suggest_idea(callback: CallbackQuery, state: FSMContext) -> None:
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
async def process_idea(message: Message, state: FSMContext, bot: Bot) -> None:
    user = message.from_user
    idea_text = message.text

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "💡 <b>Новая идея от пользователя!</b>\n\n"
            f"👤 Пользователь: <a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📝 Username: @{user.username if user.username else 'нет'}\n\n"
            f"💡 <b>Идея:</b>\n{idea_text}"
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
async def callback_report_bug(callback: CallbackQuery, state: FSMContext) -> None:
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
async def process_bug(message: Message, state: FSMContext, bot: Bot) -> None:
    user = message.from_user
    bug_text = message.text

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🐛 <b>Новый баг-репорт!</b>\n\n"
            f"👤 Пользователь: <a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📝 Username: @{user.username if user.username else 'нет'}\n\n"
            f"🐛 <b>Описание ошибки:</b>\n{bug_text}"
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
async def callback_admin_answer(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ У вас нет доступа!", show_alert=True)
        return

    user_id = int(callback.data.split("_")[1])
    await state.update_data(reply_to_user=user_id)
    await state.set_state(UserStates.waiting_admin_answer)

    await callback.message.answer(
        text=(
            f"✉️ <b>Ответ пользователю</b> <code>{user_id}</code>\n\n"
            "Напишите ответ в следующем сообщении:"
        ),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.waiting_admin_answer, F.from_user.id == ADMIN_ID)
async def process_admin_answer(message: Message, state: FSMContext, bot: Bot) -> None:
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
            text=f"❌ <b>Ошибка отправки:</b> <code>{error}</code>",
            parse_mode="HTML"
        )
