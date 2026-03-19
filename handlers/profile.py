import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from database import (
    get_user, update_user_balance, update_user_subscription,
    add_transaction, get_transaction, complete_transaction,
    get_promo_code, check_user_promo, activate_promo, add_admin_log
)
from states import ProfileForm
from keyboards import (
    profile_keyboard, payment_method_keyboard, subscription_days_keyboard,
    check_payment_keyboard, back_to_main_keyboard
)
from utils.payments import (
    create_cryptobot_invoice, check_cryptobot_invoice,
    create_xrocket_invoice, check_xrocket_invoice
)
from utils.validators import validate_amount

router = Router()
logger = logging.getLogger(__name__)

SUBSCRIPTION_PRICES = {1: 6.0, 3: 12.0, 15: 28.0}


@router.callback_query(F.data == "profile")
async def profile_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user = get_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    username = f"@{user['username']}" if user['username'] else "N/A"
    balance = user['balance']

    if user['is_subscribed'] and user['subscription_until']:
        try:
            until = datetime.fromisoformat(user['subscription_until'])
            if until > datetime.now():
                sub_text = f"Активна до {until.strftime('%d.%m.%Y')}"
            else:
                sub_text = "Отсутствует"
        except Exception:
            sub_text = "Отсутствует"
    else:
        sub_text = "Отсутствует"

    caption = (
        f"👤 Профиль\n\n"
        f"ID: {user_id}\n"
        f"Username: {username}\n"
        f"Подписка: {sub_text}\n"
        f"Баланс: {balance:.2f}$"
    )

    try:
        photo = FSInputFile("start.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=profile_keyboard()
        )
    except Exception:
        await callback.message.answer(caption, reply_markup=profile_keyboard())
    await callback.answer()


@router.callback_query(F.data == "profile_topup")
async def profile_topup(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileForm.waiting_payment_method)
    await callback.message.answer(
        "💳 Пополнение баланса\n\nВыберите метод оплаты:",
        reply_markup=payment_method_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.in_({"pay_cryptobot", "pay_xrocket"}), ProfileForm.waiting_payment_method)
async def payment_method_selected(callback: CallbackQuery, state: FSMContext):
    method = "cryptobot" if callback.data == "pay_cryptobot" else "xrocket"
    await state.update_data(payment_method=method)
    await state.set_state(ProfileForm.waiting_balance_amount)
    await callback.message.answer(
        "💵 Введите сумму для пополнения (USD):",
        reply_markup=back_to_main_keyboard()
    )
    await callback.answer()


@router.message(ProfileForm.waiting_balance_amount)
async def balance_amount_input(message: Message, state: FSMContext):
    amount = validate_amount(message.text.strip())
    if amount is None:
        await message.answer("❌ Введите корректную сумму (положительное число)")
        return

    data = await state.get_data()
    method = data.get("payment_method", "cryptobot")

    await state.clear()
    await message.answer("⏳ Создание счёта на оплату...")

    if method == "cryptobot":
        result = await create_cryptobot_invoice(amount, "Пополнение баланса Mensor")
        if result.get("ok"):
            invoice = result["result"]
            invoice_id = str(invoice["invoice_id"])
            pay_url = invoice["pay_url"]

            add_transaction(message.from_user.id, amount, "payment", invoice_id)

            await message.answer(
                f"💳 Счёт создан!\n\nСумма: {amount}$\nПерейдите по ссылке для оплаты:",
                reply_markup=check_payment_keyboard(invoice_id, "cryptobot")
            )
            await message.answer(pay_url)
        else:
            await message.answer(
                "❌ Ошибка создания счёта. Попробуйте позже.",
                reply_markup=back_to_main_keyboard()
            )
    else:
        result = await create_xrocket_invoice(amount, "Пополнение баланса Mensor")
        if result.get("success"):
            invoice_data = result["data"]
            invoice_id = str(invoice_data["id"])
            pay_url = invoice_data.get("link", "")

            add_transaction(message.from_user.id, amount, "payment", invoice_id)

            await message.answer(
                f"💳 Счёт создан!\n\nСумма: {amount}$\nПерейдите по ссылке для оплаты:",
                reply_markup=check_payment_keyboard(invoice_id, "xrocket")
            )
            await message.answer(pay_url)
        else:
            await message.answer(
                "❌ Ошибка создания счёта. Попробуйте позже.",
                reply_markup=back_to_main_keyboard()
            )


@router.callback_query(F.data.startswith("check_payment:"))
async def check_payment(callback: CallbackQuery):
    parts = callback.data.split(":")
    invoice_id = parts[1]
    method = parts[2]

    transaction = get_transaction(invoice_id)
    if not transaction:
        await callback.answer("❌ Транзакция не найдена", show_alert=True)
        return

    if transaction.get("processed"):
        await callback.answer("✅ Платёж уже был обработан!", show_alert=True)
        return

    if method == "cryptobot":
        result = await check_cryptobot_invoice(invoice_id)
        paid = (
            result.get("ok") and
            result.get("result", {}).get("items", [{}])[0].get("status") == "paid"
        )
    else:
        result = await check_xrocket_invoice(invoice_id)
        paid = result.get("success") and result.get("data", {}).get("status") == "paid"

    if paid:
        amount = transaction["amount"]
        user_id = transaction["user_id"]

        complete_transaction(invoice_id)
        update_user_balance(user_id, amount)

        username = callback.from_user.username or callback.from_user.first_name
        add_admin_log(
            "balance_topup",
            user_id,
            f"💰 Пополнение: {username}, ID: {user_id}, Сумма: {amount}$"
        )

        await callback.message.answer(f"✅ Баланс пополнен на {amount}$!")
    else:
        await callback.answer("⏳ Платёж ещё не получен. Попробуйте позже.", show_alert=True)
    await callback.answer()


@router.callback_query(F.data == "profile_subscription")
async def profile_subscription(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileForm.waiting_subscription_days)
    await callback.message.answer(
        "💎 Покупка подписки\n\nВыберите срок:",
        reply_markup=subscription_days_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub_"), ProfileForm.waiting_subscription_days)
async def subscription_days_selected(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.split("_")[1])
    price = SUBSCRIPTION_PRICES.get(days)
    if not price:
        await callback.answer("❌ Неверный период", show_alert=True)
        return

    user_id = callback.from_user.id
    user = get_user(user_id)

    if user["balance"] < price:
        await callback.answer(
            f"❌ Недостаточно средств. Нужно {price}$, у вас {user['balance']:.2f}$",
            show_alert=True
        )
        return

    update_user_balance(user_id, -price)

    now = datetime.now()
    if user["is_subscribed"] and user["subscription_until"]:
        try:
            current_until = datetime.fromisoformat(user["subscription_until"])
            if current_until > now:
                new_until = current_until + timedelta(days=days)
            else:
                new_until = now + timedelta(days=days)
        except Exception:
            new_until = now + timedelta(days=days)
    else:
        new_until = now + timedelta(days=days)

    update_user_subscription(user_id, new_until)
    await state.clear()

    username = callback.from_user.username or callback.from_user.first_name
    add_admin_log(
        "subscription_purchase",
        user_id,
        f"💎 Подписка: {username}, ID: {user_id}, {days} дней"
    )

    await callback.message.answer(
        f"✅ Подписка активирована!\nАктивна до: {new_until.strftime('%d.%m.%Y')}",
        reply_markup=back_to_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "profile_promo")
async def profile_promo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileForm.waiting_promo_code)
    await callback.message.answer(
        "🎟 Введите промокод:",
        reply_markup=back_to_main_keyboard()
    )
    await callback.answer()


@router.message(ProfileForm.waiting_promo_code)
async def promo_code_input(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    user_id = message.from_user.id

    promo = get_promo_code(code)
    if not promo:
        await message.answer("❌ Неверный промокод")
        return

    if check_user_promo(user_id, promo["id"]):
        await message.answer("❌ Вы уже активировали этот промокод")
        return

    if promo["used_count"] >= promo["max_activations"]:
        await message.answer("❌ Промокод истёк")
        return

    activate_promo(user_id, promo["id"])
    update_user_balance(user_id, promo["reward"])
    await state.clear()

    await message.answer(
        f"✅ Промокод активирован! На ваш баланс зачислено {promo['reward']}$",
        reply_markup=back_to_main_keyboard()
    )
