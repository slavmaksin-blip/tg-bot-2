import logging
import database
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from database import (
    get_user, get_products, get_product, update_user_balance,
    add_admin_log, add_email_order, get_email_order, update_email_order_status
)
from states import MailForm
from keyboards import (
    shop_keyboard, email_order_keyboard, products_keyboard,
    confirm_purchase_keyboard, back_to_main_keyboard
)
from utils.mailbuy import order_email, get_message, reorder_email
from utils.validators import validate_domain

router = Router()
logger = logging.getLogger(__name__)

MAILBUY_PRICE_MULTIPLIER = 3


@router.callback_query(F.data == "shop")
async def shop_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        photo = FSInputFile("start.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption="🛍 Магазин\n\nВыберите категорию:",
            reply_markup=shop_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "🛍 Магазин\n\nВыберите категорию:",
            reply_markup=shop_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "shop_email")
async def shop_email_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MailForm.waiting_domain)
    await callback.message.answer(
        "📧 Email Shop\n\nВведите домен сайта (например, instagram.com):",
        reply_markup=back_to_main_keyboard()
    )
    await callback.answer()


@router.message(MailForm.waiting_domain)
async def email_domain_input(message: Message, state: FSMContext):
    domain = message.text.strip().lower()
    if not validate_domain(domain):
        await message.answer("❌ Неверный формат домена. Используйте формат: site.com")
        return

    await state.clear()
    await message.answer("⏳ Поиск email адреса...")

    result = await order_email(domain)

    if result.get("status") == "success":
        order_id = result.get("id", "N/A")
        email = result.get("email", "N/A")
        api_price = result.get("price", 5)
        price = api_price * MAILBUY_PRICE_MULTIPLIER

        add_email_order(message.from_user.id, str(order_id), domain, email, price)

        caption = (
            f"📍 Сайт: {domain}\n"
            f"📮 Email: {email}\n"
            f"💸 Стоимость: {price}$\n"
            f"🧲 Код/Ссылка: ⏳ Ожидание\n"
            f"🫧 Статус: ⏳ Получение письма..."
        )
        try:
            photo = FSInputFile("start.jpg")
            await message.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=email_order_keyboard(str(order_id))
            )
        except Exception:
            await message.answer(caption, reply_markup=email_order_keyboard(str(order_id)))
    elif result.get("status") == "error":
        error_value = result.get("value", "Неизвестная ошибка")
        await message.answer(
            f"❌ Ошибка поиска: {error_value}\nПопробуйте другой домен:",
            reply_markup=back_to_main_keyboard()
        )
    else:
        await message.answer(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=back_to_main_keyboard()
        )


@router.callback_query(F.data.startswith("email_refresh:"))
async def email_refresh(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    result = await get_message(order_id)

    if result.get("status") == "success":
        msg_text = result.get("value", "")
        await callback.message.answer(f"📩 Письмо:\n{msg_text}")
    elif result.get("value") == "wait message":
        await callback.answer("⏳ Письмо ещё не пришло. Попробуйте позже.", show_alert=True)
    else:
        await callback.answer(f"❌ {result.get('value', 'Ошибка')}", show_alert=True)
    await callback.answer()


@router.callback_query(F.data.startswith("email_reorder:"))
async def email_reorder(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    result = await reorder_email(order_id)

    if result.get("status") == "success":
        new_email = result.get("email", "N/A")
        new_order_id = result.get("id", order_id)
        await callback.message.edit_caption(
            caption=f"♻️ Email пересоздан!\n📮 Новый Email: {new_email}",
            reply_markup=email_order_keyboard(str(new_order_id))
        )
    else:
        await callback.answer(f"❌ Ошибка: {result.get('value', 'Неизвестная ошибка')}", show_alert=True)
    await callback.answer()


@router.callback_query(F.data.startswith("email_getmsg:"))
async def email_getmsg(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    result = await get_message(order_id, preview=1)

    if result.get("status") == "success":
        msg_text = result.get("value", "Нет сообщений")
        await callback.message.answer(f"📩 Сообщение:\n{msg_text}")
    elif result.get("value") == "wait message":
        await callback.answer("⏳ Письмо ещё не пришло.", show_alert=True)
    else:
        await callback.answer(f"❌ {result.get('value', 'Ошибка')}", show_alert=True)
    await callback.answer()


@router.callback_query(F.data == "shop_digital")
async def shop_digital_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    products = get_products()
    if not products:
        await callback.message.answer(
            "📦 Цифровые товары\n\nТоваров нет в наличии.",
            reply_markup=back_to_main_keyboard()
        )
        await callback.answer()
        return

    try:
        photo = FSInputFile("start.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption="📦 Цифровые товары\n\nВыберите товар:",
            reply_markup=products_keyboard(products)
        )
    except Exception:
        await callback.message.answer(
            "📦 Цифровые товары\n\nВыберите товар:",
            reply_markup=products_keyboard(products)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_product:"))
async def buy_product(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    product = get_product(product_id)
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    await callback.message.answer(
        f"📦 {product['name']}\n"
        f"💸 Цена: {product['price']}$\n"
        f"📊 В наличии: {product['stock_quantity']}\n\n"
        f"Подтвердить покупку?",
        reply_markup=confirm_purchase_keyboard(product_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_buy:"))
async def confirm_buy(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    user = get_user(user_id)
    product = get_product(product_id)

    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    if product["stock_quantity"] < 1:
        await callback.answer("❌ Недостаточно товара в наличии.", show_alert=True)
        return

    if user["balance"] < product["price"]:
        await callback.answer(f"❌ Недостаточно средств. Ваш баланс: {user['balance']}$", show_alert=True)
        return

    update_user_balance(user_id, -product["price"])

    try:
        await callback.bot.send_document(user_id, product["file_id"])
    except Exception as e:
        logger.error(f"Error sending product file: {e}")
        await callback.answer("❌ Ошибка отправки файла", show_alert=True)
        return

    database.execute_query(
        "UPDATE products SET stock_quantity = stock_quantity - 1 WHERE id = ? AND stock_quantity > 0",
        (product_id,)
    )

    username = callback.from_user.username or callback.from_user.first_name
    add_admin_log(
        "product_purchase",
        user_id,
        f"📦 Покупка товара: {username}, ID: {user_id}, {product['name']} x 1"
    )

    await callback.message.answer(f"✅ Покупка успешна! Товар отправлен.")
    await callback.answer()
