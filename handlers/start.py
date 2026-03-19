import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import database as db
from config import CHANNEL_USERNAME, START_PHOTO_PATH, ADMIN_ID
from keyboards import main_menu_keyboard, subscription_keyboard

logger = logging.getLogger(__name__)
router = Router()


async def send_main_menu(message: Message, state: FSMContext, bot: Bot) -> None:
    """Send main menu with start.jpg photo."""
    await state.clear()
    try:
        photo = FSInputFile(START_PHOTO_PATH)
        await message.answer_photo(
            photo=photo,
            caption=(
                "👋 Добро пожаловать в <b>Mensor</b>!\n\n"
                "Выберите раздел:"
            ),
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await message.answer(
            "👋 Добро пожаловать в <b>Mensor</b>!\n\nВыберите раздел:",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )


async def check_subscription(bot: Bot, user_id: int) -> bool:
    """Check if user is subscribed to the required channel."""
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )
        return member.status not in ("left", "kicked", "banned")
    except Exception as e:
        logger.warning("Failed to check subscription for %d: %s", user_id, e)
        return False


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot) -> None:
    user_id = message.from_user.id
    username = message.from_user.username

    if await db.is_user_banned(user_id):
        await message.answer("🚫 Вы заблокированы в этом боте.")
        return

    await db.create_or_update_user(user_id, username)

    is_subscribed = await check_subscription(bot, user_id)
    if not is_subscribed:
        try:
            photo = FSInputFile(START_PHOTO_PATH)
            await message.answer_photo(
                photo=photo,
                caption=(
                    "📢 Для использования бота необходимо подписаться на наш канал.\n\n"
                    f"Канал: {CHANNEL_USERNAME}"
                ),
                reply_markup=subscription_keyboard(CHANNEL_USERNAME)
            )
        except FileNotFoundError:
            await message.answer(
                "📢 Для использования бота необходимо подписаться на наш канал.\n\n"
                f"Канал: {CHANNEL_USERNAME}",
                reply_markup=subscription_keyboard(CHANNEL_USERNAME)
            )
        return

    await send_main_menu(message, state, bot)


@router.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await state.clear()
    await callback.answer()
    user_id = callback.from_user.id
    username = callback.from_user.username

    if await db.is_user_banned(user_id):
        await callback.message.answer("🚫 Вы заблокированы в этом боте.")
        return

    await db.create_or_update_user(user_id, username)

    is_subscribed = await check_subscription(bot, user_id)
    if not is_subscribed:
        try:
            photo = FSInputFile(START_PHOTO_PATH)
            await callback.message.answer_photo(
                photo=photo,
                caption=(
                    "📢 Для использования бота необходимо подписаться на наш канал.\n\n"
                    f"Канал: {CHANNEL_USERNAME}"
                ),
                reply_markup=subscription_keyboard(CHANNEL_USERNAME)
            )
        except FileNotFoundError:
            await callback.message.answer(
                "📢 Для использования бота необходимо подписаться на наш канал.\n\n"
                f"Канал: {CHANNEL_USERNAME}",
                reply_markup=subscription_keyboard(CHANNEL_USERNAME)
            )
        return

    try:
        photo = FSInputFile(START_PHOTO_PATH)
        await callback.message.answer_photo(
            photo=photo,
            caption=(
                "👋 Добро пожаловать в <b>Mensor</b>!\n\n"
                "Выберите раздел:"
            ),
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await callback.message.answer(
            "👋 Добро пожаловать в <b>Mensor</b>!\n\nВыберите раздел:",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    username = callback.from_user.username
    full_name = callback.from_user.full_name

    is_subscribed = await check_subscription(bot, user_id)
    if not is_subscribed:
        await callback.answer(
            "❌ Вы не подписаны на канал! Пожалуйста, подпишитесь, чтобы продолжить.",
            show_alert=True
        )
        return

    await db.create_or_update_user(user_id, username)
    await db.add_admin_log(
        f"🆕 Новое вступление: {full_name}, ID: {user_id}",
        user_id=user_id
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            f"🆕 Новое вступление: {full_name}, ID: {user_id}"
        )
    except Exception:
        pass

    try:
        photo = FSInputFile(START_PHOTO_PATH)
        await callback.message.answer_photo(
            photo=photo,
            caption=(
                "✅ Подписка подтверждена!\n\n"
                "👋 Добро пожаловать в <b>Mensor</b>!\n\n"
                "Выберите раздел:"
            ),
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await callback.message.answer(
            "✅ Подписка подтверждена!\n\n"
            "👋 Добро пожаловать в <b>Mensor</b>!\n\nВыберите раздел:",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "menu_help")
async def callback_menu_help(callback: CallbackQuery) -> None:
    from keyboards import help_keyboard
    await callback.answer()
    try:
        photo = FSInputFile(START_PHOTO_PATH)
        await callback.message.answer_photo(
            photo=photo,
            caption=(
                "ℹ️ <b>Помощь</b>\n\n"
                "Если у вас возникли вопросы или проблемы, обратитесь в поддержку:"
            ),
            reply_markup=help_keyboard(),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await callback.message.answer(
            "ℹ️ <b>Помощь</b>\n\nЕсли у вас возникли вопросы, обратитесь в поддержку:",
            reply_markup=help_keyboard(),
            parse_mode="HTML"
        )
