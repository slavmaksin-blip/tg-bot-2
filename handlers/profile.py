import logging
from datetime import datetime, timezone
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

import database as db
from config import START_PHOTO_PATH, ADMIN_ID
from keyboards import (
    profile_keyboard, payment_method_keyboard, subscription_plans_keyboard,
    subscription_payment_method_keyboard, check_payment_keyboard, back_to_main_button
)
from states import ProfileForm
from utils.payments import (
    cryptobot_create_invoice, cryptobot_check_invoice,
    xrocket_create_invoice, xrocket_check_invoice
)
from utils.validators import validate_amount

logger = logging.getLogger(__name__)
router = Router()


def _format_subscription(sub_until: str | None) -> str:
    if not sub_until:
        return "Отсутствует"
    try:
        dt = datetime.fromisoformat(sub_until)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt > datetime.now(timezone.utc):
            return f"Активна до {dt.strftime('%d.%m.%Y')}"
    except (ValueError, TypeError):
        pass
    return "Отсутствует"


@router.callback_query(F.data == "menu_profile")
async def callback_menu_profile(callback: CallbackQuery) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await callback.message.answer("❌ Пользователь не найден.")
        return

    sub_status = _format_subscription(user.get("subscription_until"))
    username = f"@{user['username']}" if user.get("username") else "—"
    balance = float(user.get("balance", 0))

    profile_text = (
        f"👤 <b>Профиль</b>\n\n"
        f"ID: <code>{user_id}</code>\n"
        f"Username: {username}\n"
        f"Подписка: {sub_status}\n"
        f"Баланс: <b>{balance:.2f}$</b>"
    )

    try:
        photo = FSInputFile(START_PHOTO_PATH)
        await callback.message.answer_photo(
            photo=photo,
            caption=profile_text,
            reply_markup=profile_keyboard(),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await callback.message.answer(
            profile_text,
            reply_markup=profile_keyboard(),
            parse_mode="HTML"
        )


# ─── Top Up Balance ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile_topup")
async def callback_profile_topup(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProfileForm.waiting_balance_amount)
    await callback.message.answer(
        "💳 <b>Пополнение баланса</b>\n\n"
        "Введите сумму в USD (например: <code>10</code> или <code>5.50</code>):",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )


@router.message(ProfileForm.waiting_balance_amount)
async def topup_amount_received(message: Message, state: FSMContext) -> None:
    amount = validate_amount(message.text or "")
    if amount is None:
        await message.answer(
            "❌ Неверная сумма. Введите положительное число (например: <code>10</code>):",
            parse_mode="HTML"
        )
        return
    await state.update_data(topup_amount=amount)
    await state.set_state(ProfileForm.waiting_payment_method)
    await message.answer(
        f"💳 Сумма: <b>{amount}$</b>\n\nВыберите способ оплаты:",
        reply_markup=payment_method_keyboard("topup"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("pay_cryptobot:"))
async def callback_pay_cryptobot(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    context = callback.data.split(":", 1)[1]
    data = await state.get_data()
    amount = data.get("topup_amount")

    if not amount:
        await callback.message.answer("❌ Сессия истекла. Начните пополнение заново.", reply_markup=back_to_main_button())
        await state.clear()
        return

    result = await cryptobot_create_invoice(amount, "Пополнение баланса Mensor")
    if not result["success"]:
        await callback.message.answer(
            f"❌ Ошибка создания инвойса: {result.get('error', 'Неизвестная ошибка')}",
            reply_markup=back_to_main_button()
        )
        return

    invoice_id = result["invoice_id"]
    pay_url = result["pay_url"]
    user_id = callback.from_user.id

    await db.create_transaction(user_id, amount, "payment", invoice_id)
    await state.update_data(invoice_id=invoice_id, payment_type="cryptobot")

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=pay_url)],
        [InlineKeyboardButton(
            text="🔄 Проверить оплату",
            callback_data=f"check_payment:cryptobot:{invoice_id}"
        )],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])

    await callback.message.answer(
        f"🤖 <b>CryptoBot Invoice</b>\n\n"
        f"💸 Сумма: <b>{amount}$</b>\n"
        f"🆔 Инвойс: <code>{invoice_id}</code>\n\n"
        f"Нажмите кнопку для оплаты:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("pay_xrocket:"))
async def callback_pay_xrocket(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    amount = data.get("topup_amount")

    if not amount:
        await callback.message.answer("❌ Сессия истекла. Начните пополнение заново.", reply_markup=back_to_main_button())
        await state.clear()
        return

    result = await xrocket_create_invoice(amount, "Пополнение баланса Mensor")
    if not result["success"]:
        await callback.message.answer(
            f"❌ Ошибка создания инвойса: {result.get('error', 'Неизвестная ошибка')}",
            reply_markup=back_to_main_button()
        )
        return

    invoice_id = result["invoice_id"]
    pay_url = result["pay_url"]
    user_id = callback.from_user.id

    await db.create_transaction(user_id, amount, "payment", invoice_id)
    await state.update_data(invoice_id=invoice_id, payment_type="xrocket")

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Оплатить", url=pay_url)],
        [InlineKeyboardButton(
            text="🔄 Проверить оплату",
            callback_data=f"check_payment:xrocket:{invoice_id}"
        )],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])

    await callback.message.answer(
        f"🚀 <b>xRocket Invoice</b>\n\n"
        f"💸 Сумма: <b>{amount}$</b>\n"
        f"🆔 Инвойс: <code>{invoice_id}</code>\n\n"
        f"Нажмите кнопку для оплаты:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("check_payment:"))
async def callback_check_payment(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer("🔄 Проверяем оплату...")
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        return
    _, payment_type, invoice_id = parts

    if await db.is_transaction_processed(invoice_id):
        await callback.message.answer(
            "✅ Платёж уже был зачислен ранее.",
            reply_markup=back_to_main_button()
        )
        return

    if payment_type == "cryptobot":
        result = await cryptobot_check_invoice(invoice_id)
    elif payment_type == "xrocket":
        result = await xrocket_check_invoice(invoice_id)
    else:
        await callback.message.answer("❌ Неизвестный тип платежа.", reply_markup=back_to_main_button())
        return

    if not result.get("success"):
        await callback.message.answer(
            f"❌ Ошибка проверки: {result.get('error', 'Неизвестная ошибка')}",
            reply_markup=back_to_main_button()
        )
        return

    if not result.get("paid"):
        await callback.message.answer(
            "⏳ Оплата ещё не получена. Попробуйте позже.",
            reply_markup=check_payment_keyboard(invoice_id, payment_type)
        )
        return

    tx = await db.get_transaction_by_invoice(invoice_id)
    if not tx or tx.get("processed"):
        await callback.message.answer("✅ Платёж уже был зачислен.", reply_markup=back_to_main_button())
        return

    amount = float(tx["amount"])
    user_id = callback.from_user.id
    username = callback.from_user.username or str(user_id)

    await db.mark_transaction_processed(invoice_id)
    new_balance = await db.update_balance(user_id, amount)

    await db.add_admin_log(
        f"💰 Пополнение: @{username}, ID: {user_id}, Сумма: {amount}$",
        user_id=user_id
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            f"💰 Пополнение: @{username}, ID: {user_id}, Сумма: {amount}$"
        )
    except Exception:
        pass

    await callback.message.answer(
        f"✅ <b>Баланс пополнен!</b>\n\n"
        f"💸 Зачислено: <b>{amount}$</b>\n"
        f"💰 Новый баланс: <b>{new_balance:.2f}$</b>",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )
    await state.clear()


# ─── Subscription ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile_subscription")
async def callback_profile_subscription(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        photo = FSInputFile(START_PHOTO_PATH)
        await callback.message.answer_photo(
            photo=photo,
            caption=(
                "💎 <b>Купить подписку</b>\n\n"
                "Выберите период подписки:"
            ),
            reply_markup=subscription_plans_keyboard(),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await callback.message.answer(
            "💎 <b>Купить подписку</b>\n\nВыберите период подписки:",
            reply_markup=subscription_plans_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("sub_plan:"))
async def callback_sub_plan(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = callback.data.split(":")
    if len(parts) < 3:
        return
    days = int(parts[1])
    price = float(parts[2])

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    await state.update_data(sub_days=days, sub_price=price)

    if balance >= price:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"✅ Купить за {price}$ (с баланса)",
                callback_data=f"sub_buy_balance:{days}:{price}"
            )],
            [InlineKeyboardButton(
                text="🤖 CryptoBot",
                callback_data=f"sub_pay_cryptobot:{days}:{price}"
            )],
            [InlineKeyboardButton(
                text="🚀 xRocket",
                callback_data=f"sub_pay_xrocket:{days}:{price}"
            )],
            [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
        ])
    else:
        keyboard = subscription_payment_method_keyboard(days, price)

    await callback.message.answer(
        f"💎 <b>Подписка на {days} {'день' if days == 1 else 'дней'}</b>\n\n"
        f"💸 Стоимость: <b>{price}$</b>\n"
        f"💰 Ваш баланс: <b>{balance:.2f}$</b>\n\n"
        f"Выберите способ оплаты:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("sub_buy_balance:"))
async def callback_sub_buy_balance(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer()
    parts = callback.data.split(":")
    days = int(parts[1])
    price = float(parts[2])

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < price:
        await callback.message.answer(
            f"❌ Недостаточно средств.\n"
            f"💸 Нужно: {price}$\n"
            f"💰 Баланс: {balance:.2f}$",
            reply_markup=back_to_main_button()
        )
        return

    await db.update_balance(user_id, -price)
    expiry = await db.add_subscription(user_id, days)
    await db.create_transaction(user_id, -price, "purchase")

    username = callback.from_user.username or str(user_id)
    await db.add_admin_log(
        f"💎 Подписка: @{username}, ID: {user_id}, {days} дней, {price}$",
        user_id=user_id
    )

    await callback.message.answer(
        f"✅ <b>Подписка активирована!</b>\n\n"
        f"📅 Период: <b>{days} {'день' if days == 1 else 'дней'}</b>\n"
        f"📆 Действует до: <b>{expiry.strftime('%d.%m.%Y')}</b>",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )
    await state.clear()


@router.callback_query(F.data.startswith("sub_pay_cryptobot:"))
async def callback_sub_pay_cryptobot(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = callback.data.split(":")
    days = int(parts[1])
    price = float(parts[2])

    result = await cryptobot_create_invoice(price, f"Подписка Mensor на {days} дней")
    if not result["success"]:
        await callback.message.answer(
            f"❌ Ошибка создания инвойса: {result.get('error')}",
            reply_markup=back_to_main_button()
        )
        return

    invoice_id = result["invoice_id"]
    pay_url = result["pay_url"]
    user_id = callback.from_user.id

    await db.create_transaction(user_id, price, "payment", invoice_id)
    await state.update_data(invoice_id=invoice_id, sub_days=days, sub_price=price, payment_for="subscription")

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=pay_url)],
        [InlineKeyboardButton(
            text="🔄 Проверить оплату",
            callback_data=f"check_sub_payment:cryptobot:{invoice_id}:{days}:{price}"
        )],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])

    await callback.message.answer(
        f"🤖 <b>CryptoBot — Подписка на {days} дней</b>\n\n"
        f"💸 Сумма: <b>{price}$</b>\n"
        f"🆔 Инвойс: <code>{invoice_id}</code>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("sub_pay_xrocket:"))
async def callback_sub_pay_xrocket(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = callback.data.split(":")
    days = int(parts[1])
    price = float(parts[2])

    result = await xrocket_create_invoice(price, f"Подписка Mensor на {days} дней")
    if not result["success"]:
        await callback.message.answer(
            f"❌ Ошибка создания инвойса: {result.get('error')}",
            reply_markup=back_to_main_button()
        )
        return

    invoice_id = result["invoice_id"]
    pay_url = result["pay_url"]
    user_id = callback.from_user.id

    await db.create_transaction(user_id, price, "payment", invoice_id)
    await state.update_data(invoice_id=invoice_id, sub_days=days, sub_price=price, payment_for="subscription")

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Оплатить", url=pay_url)],
        [InlineKeyboardButton(
            text="🔄 Проверить оплату",
            callback_data=f"check_sub_payment:xrocket:{invoice_id}:{days}:{price}"
        )],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])

    await callback.message.answer(
        f"🚀 <b>xRocket — Подписка на {days} дней</b>\n\n"
        f"💸 Сумма: <b>{price}$</b>\n"
        f"🆔 Инвойс: <code>{invoice_id}</code>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("check_sub_payment:"))
async def callback_check_sub_payment(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer("🔄 Проверяем оплату...")
    parts = callback.data.split(":")
    if len(parts) < 5:
        return
    _, payment_type, invoice_id, days_str, price_str = parts[:5]
    days = int(days_str)
    price = float(price_str)

    if await db.is_transaction_processed(invoice_id):
        await callback.message.answer("✅ Подписка уже активирована ранее.", reply_markup=back_to_main_button())
        return

    if payment_type == "cryptobot":
        result = await cryptobot_check_invoice(invoice_id)
    elif payment_type == "xrocket":
        result = await xrocket_check_invoice(invoice_id)
    else:
        return

    if not result.get("success"):
        await callback.message.answer(
            f"❌ Ошибка проверки: {result.get('error')}",
            reply_markup=back_to_main_button()
        )
        return

    if not result.get("paid"):
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔄 Проверить оплату",
                callback_data=callback.data
            )],
            [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
        ])
        await callback.message.answer("⏳ Оплата ещё не получена. Попробуйте позже.", reply_markup=keyboard)
        return

    tx = await db.get_transaction_by_invoice(invoice_id)
    if not tx or tx.get("processed"):
        await callback.message.answer("✅ Подписка уже активирована.", reply_markup=back_to_main_button())
        return

    user_id = callback.from_user.id
    username = callback.from_user.username or str(user_id)

    await db.mark_transaction_processed(invoice_id)
    expiry = await db.add_subscription(user_id, days)

    await db.add_admin_log(
        f"💎 Подписка оплачена: @{username}, ID: {user_id}, {days} дней, {price}$",
        user_id=user_id
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            f"💎 Подписка оплачена: @{username}, ID: {user_id}, {days} дней, {price}$"
        )
    except Exception:
        pass

    await callback.message.answer(
        f"✅ <b>Подписка активирована!</b>\n\n"
        f"📅 Период: <b>{days} {'день' if days == 1 else 'дней'}</b>\n"
        f"📆 Действует до: <b>{expiry.strftime('%d.%m.%Y')}</b>",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )
    await state.clear()


# ─── Promo Codes ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile_promo")
async def callback_profile_promo(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProfileForm.waiting_promo_code)
    await callback.message.answer(
        "🎟 <b>Промокод</b>\n\n"
        "Введите ваш промокод:",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )


@router.message(ProfileForm.waiting_promo_code)
async def promo_code_received(message: Message, state: FSMContext) -> None:
    code = message.text.strip() if message.text else ""
    if not code:
        await message.answer("❌ Введите промокод:")
        return

    promo = await db.get_promo_code(code)
    if not promo:
        await message.answer(
            "❌ Промокод не найден или истёк.",
            reply_markup=back_to_main_button()
        )
        await state.clear()
        return

    user_id = message.from_user.id
    promo_id = promo["id"]

    if await db.has_user_used_promo(user_id, promo_id):
        await message.answer(
            "❌ Вы уже активировали этот промокод.",
            reply_markup=back_to_main_button()
        )
        await state.clear()
        return

    if promo["used_count"] >= promo["max_activations"]:
        await message.answer(
            "❌ Лимит активаций промокода исчерпан.",
            reply_markup=back_to_main_button()
        )
        await state.clear()
        return

    reward = float(promo["reward"])
    await db.use_promo_code(user_id, promo_id)
    await db.update_balance(user_id, reward)
    await db.delete_promo_if_exhausted(promo_id)
    await db.create_transaction(user_id, reward, "promo")

    await message.answer(
        f"✅ <b>Промокод активирован!</b>\n\n"
        f"💰 На ваш баланс зачислено: <b>{reward}$</b>",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )
    await state.clear()
