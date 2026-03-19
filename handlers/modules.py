import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from database import check_subscription as db_check_sub, add_admin_log
from states import SMSForm
from keyboards import modules_keyboard, back_to_main_keyboard
from utils.smssend import send_sms, SMSSEND_STATUS_CODES
from utils.validators import validate_swiss_phone, validate_sender_name, validate_sms_text

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "modules")
async def modules_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id

    is_sub = db_check_sub(user_id)
    if not is_sub:
        await callback.message.answer(
            "❌ У вас нет активной подписки. Пожалуйста, приобретите её в профиле.",
            reply_markup=back_to_main_keyboard()
        )
        await callback.answer()
        return

    try:
        photo = FSInputFile("start.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption="🛠 Модули\n\nВыберите страну:",
            reply_markup=modules_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "🛠 Модули\n\nВыберите страну:",
            reply_markup=modules_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "module_wip")
async def module_wip(callback: CallbackQuery):
    await callback.answer("⚠️ Данный модуль находится в разработке.", show_alert=True)


@router.callback_query(F.data == "module_switzerland")
async def module_switzerland(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SMSForm.waiting_phone)
    await callback.message.answer(
        "📱 SMS - Швейцария\n\nВведите номер телефона в формате +41xxxxxxxxx:",
        reply_markup=back_to_main_keyboard()
    )
    await callback.answer()


@router.message(SMSForm.waiting_phone)
async def sms_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not validate_swiss_phone(phone):
        await message.answer("❌ Неверный формат номера. Используйте +41xxxxxxxxx (9 цифр после +41)")
        return
    await state.update_data(phone=phone)
    await state.set_state(SMSForm.waiting_sender_name)
    await message.answer(
        "✏️ Введите имя отправителя (макс. 12 символов):",
        reply_markup=back_to_main_keyboard()
    )


@router.message(SMSForm.waiting_sender_name)
async def sms_sender(message: Message, state: FSMContext):
    sender = message.text.strip()
    if not validate_sender_name(sender):
        await message.answer("❌ Имя отправителя не должно превышать 12 символов")
        return
    await state.update_data(sender=sender)
    await state.set_state(SMSForm.waiting_message_text)
    await message.answer(
        "💬 Введите текст сообщения (макс. 160 символов):",
        reply_markup=back_to_main_keyboard()
    )


@router.message(SMSForm.waiting_message_text)
async def sms_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if not validate_sms_text(text):
        await message.answer("❌ Сообщение слишком длинное (макс 160 символов)")
        return

    data = await state.get_data()
    phone = data["phone"]
    sender = data["sender"]

    await state.clear()
    await message.answer("⏳ Отправка SMS...")

    result = await send_sms(phone, sender, text)

    status = result.get("status", -99)
    if status == 0:
        sms_array = result.get("array", [])
        sms_id = sms_array[0][1] if sms_array else "N/A"
        await message.answer(f"✅ SMS успешно отправлена! ID: {sms_id}")

        username = message.from_user.username or message.from_user.first_name
        add_admin_log(
            "sms_sent",
            message.from_user.id,
            f"📱 Отправка SMS: {username}, ID: {message.from_user.id}, Number: {phone}"
        )
    else:
        error_msg = SMSSEND_STATUS_CODES.get(status, f"Неизвестная ошибка (код {status})")
        await message.answer(f"❌ Ошибка отправки SMS: {error_msg}")

    await message.answer(
        "Вернуться в меню:",
        reply_markup=back_to_main_keyboard()
    )
