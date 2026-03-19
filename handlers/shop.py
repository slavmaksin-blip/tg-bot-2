import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

import database as db
from config import START_PHOTO_PATH, ADMIN_ID
from keyboards import (
    shop_keyboard, email_shop_result_keyboard, digital_products_keyboard,
    back_to_main_button, quantity_keyboard
)
from states import MailForm
from utils.mailbuy import search_email_by_domain, get_email_message
from utils.validators import validate_domain

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "menu_shop")
async def callback_menu_shop(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        photo = FSInputFile(START_PHOTO_PATH)
        await callback.message.answer_photo(
            photo=photo,
            caption="🛍 <b>Магазин</b>\n\nВыберите категорию:",
            reply_markup=shop_keyboard(),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await callback.message.answer(
            "🛍 <b>Магазин</b>\n\nВыберите категорию:",
            reply_markup=shop_keyboard(),
            parse_mode="HTML"
        )


# ─── Email Shop ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "shop_email")
async def callback_shop_email(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(MailForm.waiting_domain)
    await callback.message.answer(
        "📧 <b>Email Shop</b>\n\n"
        "Введите домен сайта (например, <code>instagram.com</code>):",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )


@router.message(MailForm.waiting_domain)
async def mail_domain_received(message: Message, state: FSMContext) -> None:
    domain = message.text.strip().lower() if message.text else ""
    if not validate_domain(domain):
        await message.answer(
            "❌ Неверный формат домена. Попробуйте ещё раз (например, <code>instagram.com</code>):",
            parse_mode="HTML"
        )
        return

    await message.answer("⏳ Поиск email по домену...")
    result = await search_email_by_domain(domain)
    await state.update_data(domain=domain, last_email_result=result)

    await _send_email_result(message, result, domain)


async def _send_email_result(target, result: dict, domain: str) -> None:
    if result.get("success"):
        code_link = result.get("code") or result.get("link") or "—"
        text = (
            f"📍 Сайт: <code>{domain}</code>\n"
            f"📮 Email: <code>{result['email']}</code>\n"
            f"💸 Стоимость: <b>{result['price']}$</b>\n"
            f"🧲 Код/Ссылка: {code_link}\n"
            f"🫧 Статус: {result.get('status', '—')}"
        )
        await target.answer(
            text,
            reply_markup=email_shop_result_keyboard(),
            parse_mode="HTML"
        )
    else:
        await target.answer(
            f"❌ Ошибка поиска: {result.get('error', 'Неизвестная ошибка')}\n\n"
            "Попробуйте другой домен:",
            reply_markup=back_to_main_button()
        )


@router.callback_query(F.data == "email_refresh")
async def callback_email_refresh(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("🔄 Обновление...")
    data = await state.get_data()
    domain = data.get("domain")
    if not domain:
        await callback.message.answer("❌ Сессия истекла. Начните поиск заново.", reply_markup=back_to_main_button())
        return
    result = await search_email_by_domain(domain)
    await state.update_data(last_email_result=result)
    await _send_email_result(callback.message, result, domain)


@router.callback_query(F.data == "email_recreate")
async def callback_email_recreate(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("♻️ Пересоздание...")
    data = await state.get_data()
    domain = data.get("domain")
    if not domain:
        await callback.message.answer("❌ Сессия истекла. Начните поиск заново.", reply_markup=back_to_main_button())
        return
    result = await search_email_by_domain(domain)
    await state.update_data(last_email_result=result)
    await _send_email_result(callback.message, result, domain)


@router.callback_query(F.data == "email_get_message")
async def callback_email_get_message(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("📩 Получение сообщений...")
    data = await state.get_data()
    last_result = data.get("last_email_result", {})
    email = last_result.get("email")

    if not email or email == "—":
        await callback.message.answer("❌ Email не найден. Сначала выполните поиск.", reply_markup=back_to_main_button())
        return

    result = await get_email_message(email)
    if result.get("success"):
        messages = result.get("messages", [])
        if messages:
            msgs_text = "\n\n".join(
                f"📨 От: {m.get('from', '—')}\n📝 {m.get('subject', '—')}\n{m.get('body', '—')[:200]}"
                for m in messages[:3]
            )
            await callback.message.answer(
                f"📩 <b>Сообщения для {email}:</b>\n\n{msgs_text}",
                reply_markup=email_shop_result_keyboard(),
                parse_mode="HTML"
            )
        else:
            await callback.message.answer(
                f"📭 Нет новых сообщений для <code>{email}</code>",
                reply_markup=email_shop_result_keyboard(),
                parse_mode="HTML"
            )
    else:
        await callback.message.answer(
            f"❌ Ошибка получения сообщений: {result.get('error', 'Неизвестная ошибка')}",
            reply_markup=email_shop_result_keyboard()
        )


# ─── Digital Products ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "shop_digital")
async def callback_shop_digital(callback: CallbackQuery) -> None:
    await callback.answer()
    products = await db.get_all_products_grouped()

    if not products:
        await callback.message.answer(
            "🛒 <b>Цифровые товары</b>\n\n"
            "❌ На данный момент товары недоступны.",
            reply_markup=back_to_main_button(),
            parse_mode="HTML"
        )
        return

    try:
        photo = FSInputFile(START_PHOTO_PATH)
        await callback.message.answer_photo(
            photo=photo,
            caption="🛒 <b>Цифровые товары</b>\n\nВыберите товар:",
            reply_markup=digital_products_keyboard(products),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await callback.message.answer(
            "🛒 <b>Цифровые товары</b>\n\nВыберите товар:",
            reply_markup=digital_products_keyboard(products),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("buy_product:"))
async def callback_buy_product(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        return
    _, product_name, category = parts

    stock = await db.get_product_stock(product_name, category)
    price = await db.get_product_price(product_name, category)

    if stock == 0 or price is None:
        await callback.message.answer(
            "❌ Недостаточно товара в наличии.",
            reply_markup=back_to_main_button()
        )
        return

    await state.update_data(product_name=product_name, category=category, price=price)
    await callback.message.answer(
        f"🛒 <b>{product_name}</b>\n\n"
        f"💸 Цена: <b>{price}$</b> за единицу\n"
        f"📦 В наличии: <b>{stock}</b> шт.\n\n"
        f"Выберите количество:",
        reply_markup=quantity_keyboard(stock, product_name, category),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("qty:"))
async def callback_quantity_selected(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer()
    parts = callback.data.split(":", 3)
    if len(parts) < 4:
        return
    _, qty_str, product_name, category = parts

    try:
        quantity = int(qty_str)
    except ValueError:
        return

    data = await state.get_data()
    price = data.get("price")
    if price is None:
        price = await db.get_product_price(product_name, category)
    if price is None:
        await callback.message.answer("❌ Товар не найден.", reply_markup=back_to_main_button())
        return

    total_cost = round(float(price) * quantity, 2)
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < total_cost:
        await callback.message.answer(
            f"❌ Недостаточно средств.\n\n"
            f"💸 Стоимость: <b>{total_cost}$</b>\n"
            f"💰 Ваш баланс: <b>{balance:.2f}$</b>",
            reply_markup=back_to_main_button(),
            parse_mode="HTML"
        )
        return

    stock = await db.get_product_stock(product_name, category)
    if stock < quantity:
        await callback.message.answer(
            "❌ Недостаточно товара в наличии.",
            reply_markup=back_to_main_button()
        )
        return

    file_ids = await db.purchase_product_items(product_name, category, quantity)
    if len(file_ids) < quantity:
        await callback.message.answer(
            "❌ Недостаточно товара в наличии.",
            reply_markup=back_to_main_button()
        )
        return

    await db.update_balance(user_id, -total_cost)
    await db.create_transaction(user_id, -total_cost, "purchase")

    username = callback.from_user.username or str(user_id)
    await db.add_admin_log(
        f"📦 Покупка товара: @{username}, ID: {user_id}, {product_name} x {quantity}",
        user_id=user_id,
        details=f"Total: {total_cost}$"
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            f"📦 Покупка товара: @{username}, ID: {user_id}, {product_name} x {quantity}\n"
            f"💰 Сумма: {total_cost}$"
        )
    except Exception:
        pass

    await callback.message.answer(
        f"✅ <b>Покупка успешна!</b>\n\n"
        f"🛒 {product_name} x {quantity}\n"
        f"💰 Списано: {total_cost}$\n\n"
        f"Ваши файлы:",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )

    for file_id in file_ids:
        try:
            await bot.send_document(user_id, file_id)
        except Exception:
            try:
                await bot.send_photo(user_id, file_id)
            except Exception:
                await bot.send_message(user_id, f"📄 Файл: {file_id}")

    await state.clear()
