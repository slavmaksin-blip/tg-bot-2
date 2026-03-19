import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import CHANNEL_USERNAME, ADMIN_ID
from database import get_user, create_user, add_admin_log
from keyboards import main_menu_keyboard, subscription_keyboard, back_to_main_keyboard
from handlers.subscription import check_subscription as check_user_subscription

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    user = get_user(user_id)
    if not user:
        create_user(user_id, username)
        add_admin_log("new_user", user_id, f"New user: {username}, ID: {user_id}")

    is_subscribed = await check_user_subscription(message.bot, user_id)

    if not is_subscribed:
        await message.answer(
            "❌ Вы не подписаны на канал!\nПожалуйста, подпишитесь, чтобы продолжить.",
            reply_markup=subscription_keyboard(CHANNEL_USERNAME)
        )
        return

    try:
        photo = FSInputFile("start.jpg")
        await message.answer_photo(
            photo=photo,
            caption="👋 Добро пожаловать в Mensor!\nВыберите раздел:",
            reply_markup=main_menu_keyboard()
        )
    except Exception:
        await message.answer(
            "👋 Добро пожаловать в Mensor!\nВыберите раздел:",
            reply_markup=main_menu_keyboard()
        )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        photo = FSInputFile("start.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption="👋 Добро пожаловать в Mensor!\nВыберите раздел:",
            reply_markup=main_menu_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "👋 Добро пожаловать в Mensor!\nВыберите раздел:",
            reply_markup=main_menu_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name

    is_subscribed = await check_user_subscription(callback.bot, user_id)

    if not is_subscribed:
        await callback.answer("❌ Вы всё ещё не подписаны на канал!", show_alert=True)
        return

    add_admin_log("subscription_check", user_id, f"🆕 Новое вступление: {username}, ID: {user_id}")

    try:
        photo = FSInputFile("start.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption="✅ Подписка подтверждена!\n\n👋 Добро пожаловать в Mensor!\nВыберите раздел:",
            reply_markup=main_menu_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "✅ Подписка подтверждена!\n\n👋 Добро пожаловать в Mensor!\nВыберите раздел:",
            reply_markup=main_menu_keyboard()
        )
    await callback.answer()
