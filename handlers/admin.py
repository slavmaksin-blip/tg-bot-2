import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database import (
    get_user, get_all_users, ban_user, add_admin_log,
    add_product, get_products, delete_product,
    update_user_balance, add_promo_code
)
from states import AdminForm
from keyboards import (
    admin_keyboard, admin_products_keyboard, admin_broadcast_type_keyboard,
    admin_balance_operation_keyboard, back_to_main_keyboard
)

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    await state.clear()
    try:
        photo = FSInputFile("start.jpg")
        await message.answer_photo(
            photo=photo,
            caption="🔐 Админ-панель",
            reply_markup=admin_keyboard()
        )
    except Exception:
        await message.answer("🔐 Админ-панель", reply_markup=admin_keyboard())


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await state.clear()
    try:
        photo = FSInputFile("start.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption="🔐 Админ-панель",
            reply_markup=admin_keyboard()
        )
    except Exception:
        await callback.message.answer("🔐 Админ-панель", reply_markup=admin_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_ban")
async def admin_ban(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await state.set_state(AdminForm.waiting_ban_user_id)
    await callback.message.answer("🚫 Введите ID пользователя для бана:", reply_markup=back_to_main_keyboard())
    await callback.answer()


@router.message(AdminForm.waiting_ban_user_id)
async def ban_user_input(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный ID")
        return

    ban_user(target_id, True)
    add_admin_log("ban_user", message.from_user.id, f"Banned user ID: {target_id}")
    await state.clear()
    await message.answer(f"✅ Пользователь {target_id} заблокирован.", reply_markup=back_to_main_keyboard())


@router.callback_query(F.data == "admin_unban")
async def admin_unban(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await state.set_state(AdminForm.waiting_unban_user_id)
    await callback.message.answer("✅ Введите ID пользователя для разбана:", reply_markup=back_to_main_keyboard())
    await callback.answer()


@router.message(AdminForm.waiting_unban_user_id)
async def unban_user_input(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный ID")
        return

    ban_user(target_id, False)
    add_admin_log("unban_user", message.from_user.id, f"Unbanned user ID: {target_id}")
    await state.clear()
    await message.answer(f"✅ Пользователь {target_id} разблокирован.", reply_markup=back_to_main_keyboard())


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await state.set_state(AdminForm.waiting_broadcast_type)
    await callback.message.answer("📢 Рассылка\n\nВыберите тип:", reply_markup=admin_broadcast_type_keyboard())
    await callback.answer()


@router.callback_query(F.data == "broadcast_text", AdminForm.waiting_broadcast_type)
async def broadcast_text_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(broadcast_type="text")
    await state.set_state(AdminForm.waiting_broadcast_content)
    await callback.message.answer("📝 Введите текст для рассылки:", reply_markup=back_to_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "broadcast_photo", AdminForm.waiting_broadcast_type)
async def broadcast_photo_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(broadcast_type="photo")
    await state.set_state(AdminForm.waiting_broadcast_photo)
    await callback.message.answer("🖼️ Отправьте фото для рассылки:", reply_markup=back_to_main_keyboard())
    await callback.answer()


@router.message(AdminForm.waiting_broadcast_photo)
async def broadcast_photo_received(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото")
        return
    photo_id = message.photo[-1].file_id
    await state.update_data(broadcast_photo_id=photo_id)
    await state.set_state(AdminForm.waiting_broadcast_caption)
    await message.answer(
        "💬 Введите подпись к фото (или отправьте /skip для пропуска):",
        reply_markup=back_to_main_keyboard()
    )


@router.message(AdminForm.waiting_broadcast_caption)
async def broadcast_caption_received(message: Message, state: FSMContext):
    caption = "" if message.text == "/skip" else message.text
    data = await state.get_data()
    photo_id = data.get("broadcast_photo_id")
    await state.clear()

    users = get_all_users()
    sent = 0
    for user in users:
        if user.get("is_banned"):
            continue
        try:
            await message.bot.send_photo(user["user_id"], photo_id, caption=caption)
            sent += 1
        except Exception:
            pass

    add_admin_log("broadcast", message.from_user.id, f"Photo broadcast to {sent} users")
    await message.answer(f"✅ Рассылка завершена! Отправлено: {sent} пользователям.", reply_markup=back_to_main_keyboard())


@router.message(AdminForm.waiting_broadcast_content)
async def broadcast_content(message: Message, state: FSMContext):
    text = message.text
    await state.clear()

    users = get_all_users()
    sent = 0
    for user in users:
        if user.get("is_banned"):
            continue
        try:
            await message.bot.send_message(user["user_id"], text)
            sent += 1
        except Exception:
            pass

    add_admin_log("broadcast", message.from_user.id, f"Text broadcast to {sent} users")
    await message.answer(f"✅ Рассылка завершена! Отправлено: {sent} пользователям.", reply_markup=back_to_main_keyboard())


@router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await state.clear()
    await callback.message.answer("📦 Управление товарами:", reply_markup=admin_products_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_product_add")
async def admin_product_add(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await state.set_state(AdminForm.waiting_product_category)
    await callback.message.answer(
        "📁 Введите категорию товара (Text, Email, Crypto и т.д.):",
        reply_markup=back_to_main_keyboard()
    )
    await callback.answer()


@router.message(AdminForm.waiting_product_category)
async def product_category_input(message: Message, state: FSMContext):
    await state.update_data(product_category=message.text.strip())
    await state.set_state(AdminForm.waiting_product_name)
    await message.answer("🏷️ Введите название товара:", reply_markup=back_to_main_keyboard())


@router.message(AdminForm.waiting_product_name)
async def product_name_input(message: Message, state: FSMContext):
    await state.update_data(product_name=message.text.strip())
    await state.set_state(AdminForm.waiting_product_price)
    await message.answer("💵 Введите цену товара (USD):", reply_markup=back_to_main_keyboard())


@router.message(AdminForm.waiting_product_price)
async def product_price_input(message: Message, state: FSMContext):
    from utils.validators import validate_amount
    price = validate_amount(message.text.strip())
    if price is None:
        await message.answer("❌ Введите корректную цену")
        return
    await state.update_data(product_price=price)
    await state.set_state(AdminForm.waiting_product_file)
    await message.answer(
        "📎 Отправьте файл товара (для нескольких отправляйте по одному, /done для завершения):",
        reply_markup=back_to_main_keyboard()
    )


@router.message(AdminForm.waiting_product_file, F.document)
async def product_file_input(message: Message, state: FSMContext):
    file_id = message.document.file_id
    data = await state.get_data()

    name = data.get("product_name", "Product")
    category = data.get("product_category", "General")
    price = data.get("product_price", 0)

    add_product(name, category, price, file_id)
    add_admin_log("add_product", message.from_user.id, f"Added product: {name}, price: {price}$")

    await message.answer("✅ Файл добавлен! Отправьте ещё или введите /done для завершения.")


@router.message(AdminForm.waiting_product_file, F.text == "/done")
async def product_file_done(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Добавление товара завершено!", reply_markup=back_to_main_keyboard())


@router.callback_query(F.data == "admin_product_list")
async def admin_product_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    products = get_products()
    if not products:
        await callback.message.answer("📦 Нет товаров.", reply_markup=back_to_main_keyboard())
    else:
        text = "📦 Список товаров:\n\n"
        for p in products:
            text += f"ID: {p['id']} | {p['name']} | {p['price']}$ | Stock: {p['stock_quantity']}\n"
        await callback.message.answer(text, reply_markup=back_to_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_product_delete")
async def admin_product_delete(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await state.set_state(AdminForm.waiting_delete_product_id)
    products = get_products()
    text = "🗑️ Введите ID товара для удаления:\n\n"
    for p in products:
        text += f"ID: {p['id']} | {p['name']} | Stock: {p['stock_quantity']}\n"
    await callback.message.answer(text, reply_markup=back_to_main_keyboard())
    await callback.answer()


@router.message(AdminForm.waiting_delete_product_id)
async def delete_product_input(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        product_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный ID")
        return

    delete_product(product_id)
    add_admin_log("delete_product", message.from_user.id, f"Deleted product ID: {product_id}")
    await state.clear()
    await message.answer(f"✅ Товар {product_id} удалён.", reply_markup=back_to_main_keyboard())


@router.callback_query(F.data == "admin_balance")
async def admin_balance(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await state.set_state(AdminForm.waiting_balance_user_id)
    await callback.message.answer("💵 Введите ID пользователя:", reply_markup=back_to_main_keyboard())
    await callback.answer()


@router.message(AdminForm.waiting_balance_user_id)
async def balance_user_id_input(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный ID")
        return

    await state.update_data(balance_target_id=target_id)
    await state.set_state(AdminForm.waiting_balance_operation)
    await message.answer("💵 Выберите операцию:", reply_markup=admin_balance_operation_keyboard())


@router.callback_query(F.data.in_({"balance_add", "balance_sub"}), AdminForm.waiting_balance_operation)
async def balance_operation_selected(callback: CallbackQuery, state: FSMContext):
    operation = "add" if callback.data == "balance_add" else "sub"
    await state.update_data(balance_operation=operation)
    await state.set_state(AdminForm.waiting_balance_amount)
    await callback.message.answer("💵 Введите сумму (USD):", reply_markup=back_to_main_keyboard())
    await callback.answer()


@router.message(AdminForm.waiting_balance_amount)
async def admin_balance_amount_input(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    from utils.validators import validate_amount
    amount = validate_amount(message.text.strip())
    if amount is None:
        await message.answer("❌ Введите корректную сумму")
        return

    data = await state.get_data()
    target_id = data.get("balance_target_id")
    operation = data.get("balance_operation", "add")

    if operation == "sub":
        amount = -amount

    update_user_balance(target_id, amount)
    add_admin_log("balance_change", message.from_user.id, f"Balance {operation}: user {target_id}, amount {abs(amount)}$")
    await state.clear()

    op_text = "добавлено" if operation == "add" else "вычтено"
    await message.answer(f"✅ Баланс изменён. {op_text}: {abs(amount)}$", reply_markup=back_to_main_keyboard())


@router.callback_query(F.data == "admin_balances")
async def admin_balances_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    users = get_all_users()
    if not users:
        await callback.message.answer("📊 Нет пользователей.", reply_markup=back_to_main_keyboard())
        await callback.answer()
        return

    text = "📊 Список балансов:\n\n"
    text += "Username | ID | Balance | Подписка\n"
    text += "-" * 40 + "\n"

    for user in users:
        username = f"@{user['username']}" if user['username'] else "N/A"
        balance = user['balance']
        is_sub = "Активна" if user.get('is_subscribed') else "Отсутствует"
        text += f"{username} | {user['user_id']} | {balance:.2f}$ | {is_sub}\n"

    if len(text) > 4096:
        # Split at newlines to avoid breaking multi-byte characters mid-sequence
        lines = text.split("\n")
        chunk = ""
        for line in lines:
            if len(chunk) + len(line) + 1 > 4096:
                await callback.message.answer(chunk)
                chunk = line + "\n"
            else:
                chunk += line + "\n"
        if chunk:
            await callback.message.answer(chunk, reply_markup=back_to_main_keyboard())
    else:
        await callback.message.answer(text, reply_markup=back_to_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_promo")
async def admin_promo(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await state.set_state(AdminForm.waiting_promo_code)
    await callback.message.answer("🎫 Введите код промокода:", reply_markup=back_to_main_keyboard())
    await callback.answer()


@router.message(AdminForm.waiting_promo_code)
async def admin_promo_code_input(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    code = message.text.strip().upper()
    await state.update_data(new_promo_code=code)
    await state.set_state(AdminForm.waiting_promo_reward)
    await message.answer("💰 Введите награду (USD):", reply_markup=back_to_main_keyboard())


@router.message(AdminForm.waiting_promo_reward)
async def admin_promo_reward_input(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    from utils.validators import validate_amount
    reward = validate_amount(message.text.strip())
    if reward is None:
        await message.answer("❌ Введите корректную сумму")
        return
    await state.update_data(new_promo_reward=reward)
    await state.set_state(AdminForm.waiting_promo_max_activations)
    await message.answer("🔢 Введите максимальное количество активаций:", reply_markup=back_to_main_keyboard())


@router.message(AdminForm.waiting_promo_max_activations)
async def admin_promo_max_activations_input(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        max_act = int(message.text.strip())
        if max_act <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число")
        return

    data = await state.get_data()
    code = data.get("new_promo_code")
    reward = data.get("new_promo_reward")

    add_promo_code(code, reward, max_act, message.from_user.id)
    add_admin_log("create_promo", message.from_user.id, f"Created promo: {code}, reward: {reward}$, max: {max_act}")
    await state.clear()

    await message.answer(
        f"✅ Промокод создан!\nКод: {code}\nНаграда: {reward}$\nМакс. активаций: {max_act}",
        reply_markup=back_to_main_keyboard()
    )
