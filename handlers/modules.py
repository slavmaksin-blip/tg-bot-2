import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

import database as db
from config import START_PHOTO_PATH
from keyboards import (
    modules_keyboard, sms_country_keyboard, back_to_main_button,
    confirm_sms_keyboard
)
from states import SMSForm
from utils.smssend import send_sms
from utils.validators import validate_swiss_phone, validate_sender_name, validate_message_text

logger = logging.getLogger(__name__)
router = Router()


async def _require_subscription(user_id: int, callback: CallbackQuery) -> bool:
    """Return True if user has active subscription, otherwise send error and return False."""
    has_sub = await db.has_active_subscription(user_id)
    if not has_sub:
        await callback.answer(
            "❌ У вас нет активной подписки. Пожалуйста, приобретите её в профиле.",
            show_alert=True
        )
    return has_sub


@router.callback_query(F.data == "menu_modules")
async def callback_menu_modules(callback: CallbackQuery) -> None:
    await callback.answer()
    user_id = callback.from_user.id

    if not await _require_subscription(user_id, callback):
        return

    try:
        photo = FSInputFile(START_PHOTO_PATH)
        await callback.message.answer_photo(
            photo=photo,
            caption="🛠 <b>Модули</b>\n\nВыберите модуль:",
            reply_markup=modules_keyboard(),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await callback.message.answer(
            "🛠 <b>Модули</b>\n\nВыберите модуль:",
            reply_markup=modules_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "module_sms")
async def callback_module_sms(callback: CallbackQuery) -> None:
    await callback.answer()
    user_id = callback.from_user.id

    if not await _require_subscription(user_id, callback):
        return

    try:
        photo = FSInputFile(START_PHOTO_PATH)
        await callback.message.answer_photo(
            photo=photo,
            caption="📱 <b>SMS Модуль</b>\n\nВыберите страну:",
            reply_markup=sms_country_keyboard(),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await callback.message.answer(
            "📱 <b>SMS Модуль</b>\n\nВыберите страну:",
            reply_markup=sms_country_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "sms_country_unavailable")
async def callback_sms_country_unavailable(callback: CallbackQuery) -> None:
    await callback.answer("❌ Данная страна временно недоступна.", show_alert=True)


@router.callback_query(F.data == "sms_country_switzerland")
async def callback_sms_country_switzerland(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(SMSForm.waiting_phone)
    await callback.message.answer(
        "📱 <b>SMS для Швейцарии</b>\n\n"
        "Введите номер телефона в формате <code>+41xxxxxxx</code>:",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )


@router.message(SMSForm.waiting_phone)
async def sms_phone_received(message: Message, state: FSMContext) -> None:
    phone = message.text.strip() if message.text else ""
    if not validate_swiss_phone(phone):
        await message.answer(
            "❌ Неверный формат номера. Введите номер в формате <code>+41xxxxxxx</code>:",
            parse_mode="HTML"
        )
        return
    await state.update_data(phone=phone)
    await state.set_state(SMSForm.waiting_sender_name)
    await message.answer(
        "✏️ Введите имя отправителя (макс. 12 символов):",
        reply_markup=back_to_main_button()
    )


@router.message(SMSForm.waiting_sender_name)
async def sms_sender_received(message: Message, state: FSMContext) -> None:
    sender = message.text.strip() if message.text else ""
    if not validate_sender_name(sender):
        await message.answer(
            "❌ Имя отправителя должно содержать от 1 до 12 символов. Попробуйте ещё раз:"
        )
        return
    await state.update_data(sender=sender)
    await state.set_state(SMSForm.waiting_message_text)
    await message.answer(
        "📝 Введите текст сообщения (макс. 160 символов):",
        reply_markup=back_to_main_button()
    )


@router.message(SMSForm.waiting_message_text)
async def sms_message_received(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    if not validate_message_text(text):
        await message.answer(
            "❌ Текст сообщения должен содержать от 1 до 160 символов. Попробуйте ещё раз:"
        )
        return
    await state.update_data(message_text=text)
    data = await state.get_data()

    await state.set_state(SMSForm.waiting_country)
    await message.answer(
        f"📋 <b>Подтверждение отправки SMS</b>\n\n"
        f"📞 Номер: <code>{data['phone']}</code>\n"
        f"👤 Отправитель: <code>{data['sender']}</code>\n"
        f"📝 Сообщение: {data['message_text']}\n\n"
        f"Подтвердите отправку:",
        reply_markup=confirm_sms_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "sms_confirm_send")
async def sms_confirm_send(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    phone = data.get("phone", "")
    sender = data.get("sender", "")
    message_text = data.get("message_text", "")

    if not all([phone, sender, message_text]):
        await callback.message.answer(
            "❌ Данные утеряны. Пожалуйста, начните отправку SMS заново.",
            reply_markup=back_to_main_button()
        )
        await state.clear()
        return

    await callback.message.answer("⏳ Отправка SMS...")
    result = await send_sms(phone, sender, message_text)
    await state.clear()

    if result["success"]:
        await callback.message.answer(
            f"✅ SMS успешно отправлено!\n\n"
            f"📞 На номер: <code>{phone}</code>",
            reply_markup=back_to_main_button(),
            parse_mode="HTML"
        )
        await db.add_admin_log(
            f"📱 SMS отправлено на {phone}",
            user_id=callback.from_user.id,
            details=f"Sender: {sender}, Message: {message_text[:50]}"
        )
    else:
        await callback.message.answer(
            f"❌ Ошибка отправки SMS: {result['message']}",
            reply_markup=back_to_main_button()
        )


@router.callback_query(F.data.in_({"module_mailer", "module_screen", "module_proxy"}))
async def callback_module_unavailable(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "⚠️ Данный модуль находится в разработке.",
        reply_markup=back_to_main_button()
    )
