import logging
from datetime import datetime, timezone
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_ID, START_PHOTO_PATH
from keyboards import (
    admin_panel_keyboard, admin_products_keyboard,
    admin_balance_operation_keyboard, broadcast_type_keyboard,
    back_to_main_button
)
from states import (
    AdminBanForm, AdminUnbanForm, AdminBroadcastForm,
    AdminProductForm, AdminBalanceForm, AdminPromoForm
)
from utils.validators import validate_amount, validate_positive_int

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


async def _send_admin_panel(target, user_id: int) -> None:
    if not is_admin(user_id):
        await target.answer("🚫 Доступ запрещён.")
        return
    try:
        photo = FSInputFile(START_PHOTO_PATH)
        await target.answer_photo(
            photo=photo,
            caption="🔧 <b>Админ-панель</b>\n\nВыберите действие:",
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )
    except (FileNotFoundError, AttributeError):
        await target.answer(
            "🔧 <b>Админ-панель</b>\n\nВыберите действие:",
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("🚫 Доступ запрещён.")
        return
    await _send_admin_panel(message, message.from_user.id)


@router.callback_query(F.data == "admin_panel")
async def callback_admin_panel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    if not is_admin(callback.from_user.id):
        await callback.answer("🚫 Доступ запрещён.", show_alert=True)
        return
    await _send_admin_panel(callback.message, callback.from_user.id)


# ─── Ban/Unban ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_ban")
async def callback_admin_ban(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminBanForm.waiting_user_id)
    await callback.message.answer(
        "🚫 <b>Забанить пользователя</b>\n\nВведите ID пользователя:",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )


@router.message(AdminBanForm.waiting_user_id)
async def admin_ban_user_id_received(message: Message, state: FSMContext, bot: Bot) -> None:
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("❌ Введите корректный числовой ID:")
        return

    await db.ban_user(target_id)
    await db.add_admin_log(f"🚫 Бан пользователя ID: {target_id}", user_id=message.from_user.id)

    try:
        await bot.send_message(target_id, "🚫 Вы были заблокированы администратором.")
    except Exception:
        pass

    await message.answer(
        f"✅ Пользователь <code>{target_id}</code> заблокирован.",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await state.clear()


@router.callback_query(F.data == "admin_unban")
async def callback_admin_unban(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminUnbanForm.waiting_user_id)
    await callback.message.answer(
        "✅ <b>Разбанить пользователя</b>\n\nВведите ID пользователя:",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )


@router.message(AdminUnbanForm.waiting_user_id)
async def admin_unban_user_id_received(message: Message, state: FSMContext, bot: Bot) -> None:
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("❌ Введите корректный числовой ID:")
        return

    await db.unban_user(target_id)
    await db.add_admin_log(f"✅ Разбан пользователя ID: {target_id}", user_id=message.from_user.id)

    try:
        await bot.send_message(target_id, "✅ Вы были разблокированы администратором.")
    except Exception:
        pass

    await message.answer(
        f"✅ Пользователь <code>{target_id}</code> разблокирован.",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await state.clear()


# ─── Broadcast ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminBroadcastForm.waiting_message_type)
    await callback.message.answer(
        "📢 <b>Рассылка</b>\n\nВыберите тип сообщения:",
        reply_markup=broadcast_type_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("broadcast_type:"))
async def callback_broadcast_type(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return
    msg_type = callback.data.split(":", 1)[1]
    await state.update_data(broadcast_type=msg_type)
    await state.set_state(AdminBroadcastForm.waiting_broadcast_content)

    if msg_type == "text":
        await callback.message.answer(
            "📝 Введите текст для рассылки:",
            reply_markup=back_to_main_button()
        )
    else:
        await callback.message.answer(
            "🖼 Отправьте фото с подписью для рассылки:",
            reply_markup=back_to_main_button()
        )


@router.message(AdminBroadcastForm.waiting_broadcast_content)
async def admin_broadcast_content_received(message: Message, state: FSMContext, bot: Bot) -> None:
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    broadcast_type = data.get("broadcast_type", "text")

    users = await db.get_all_users_not_banned()
    sent = 0
    failed = 0

    await message.answer(f"📢 Начинаю рассылку для {len(users)} пользователей...")

    for user in users:
        uid = user["user_id"]
        try:
            if broadcast_type == "photo" and message.photo:
                await bot.send_photo(
                    uid,
                    message.photo[-1].file_id,
                    caption=message.caption or ""
                )
            else:
                text = message.text or message.caption or ""
                await bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1

    await db.add_admin_log(
        f"📢 Рассылка: отправлено {sent}, ошибок {failed}",
        user_id=message.from_user.id
    )

    await message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"📨 Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}",
        reply_markup=admin_panel_keyboard()
    )
    await state.clear()


# ─── Products Management ──────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_products")
async def callback_admin_products(callback: CallbackQuery) -> None:
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer(
        "📦 <b>Управление товарами</b>",
        reply_markup=admin_products_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_add_product")
async def callback_admin_add_product(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminProductForm.waiting_category)
    await callback.message.answer(
        "📦 <b>Добавление товара</b>\n\n"
        "Введите категорию товара (например: <code>Netflix</code>):",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )


@router.message(AdminProductForm.waiting_category)
async def admin_product_category_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    category = message.text.strip() if message.text else ""
    if not category:
        await message.answer("❌ Введите название категории:")
        return
    await state.update_data(category=category)
    await state.set_state(AdminProductForm.waiting_name)
    await message.answer(
        f"📦 Категория: <b>{category}</b>\n\n"
        "Введите название товара:",
        parse_mode="HTML"
    )


@router.message(AdminProductForm.waiting_name)
async def admin_product_name_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    name = message.text.strip() if message.text else ""
    if not name:
        await message.answer("❌ Введите название товара:")
        return
    await state.update_data(name=name)
    await state.set_state(AdminProductForm.waiting_price)
    await message.answer(
        f"📦 Товар: <b>{name}</b>\n\n"
        "Введите цену в USD (например: <code>9.99</code>):",
        parse_mode="HTML"
    )


@router.message(AdminProductForm.waiting_price)
async def admin_product_price_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    price = validate_amount(message.text or "")
    if price is None:
        await message.answer("❌ Введите корректную цену (например: <code>9.99</code>):", parse_mode="HTML")
        return
    await state.update_data(price=price)
    await state.set_state(AdminProductForm.waiting_file)
    await message.answer(
        f"💸 Цена: <b>{price}$</b>\n\n"
        "Отправьте файл (документ) для этого товара:",
        parse_mode="HTML"
    )


@router.message(AdminProductForm.waiting_file)
async def admin_product_file_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return

    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
    elif message.video:
        file_id = message.video.file_id

    if not file_id:
        await message.answer("❌ Пожалуйста, отправьте файл (документ, фото или видео):")
        return

    data = await state.get_data()
    name = data.get("name", "")
    category = data.get("category", "")
    price = float(data.get("price", 0))

    await db.add_product(name, category, price, file_id)
    await db.add_admin_log(
        f"📦 Добавлен товар: {name} ({category}), {price}$",
        user_id=message.from_user.id
    )

    await message.answer(
        f"✅ Товар добавлен!\n\n"
        f"📦 Название: <b>{name}</b>\n"
        f"🏷 Категория: <b>{category}</b>\n"
        f"💸 Цена: <b>{price}$</b>",
        reply_markup=admin_products_keyboard(),
        parse_mode="HTML"
    )
    await state.clear()


# ─── Balance Management ───────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_balance")
async def callback_admin_balance(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminBalanceForm.waiting_user_id)
    await callback.message.answer(
        "💵 <b>Изменить баланс</b>\n\nВведите ID пользователя:",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )


@router.message(AdminBalanceForm.waiting_user_id)
async def admin_balance_user_id_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("❌ Введите корректный числовой ID:")
        return

    user = await db.get_user(target_id)
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return

    await state.update_data(target_user_id=target_id)
    await state.set_state(AdminBalanceForm.waiting_operation)
    await message.answer(
        f"👤 Пользователь: <code>{target_id}</code>\n"
        f"💰 Текущий баланс: <b>{float(user['balance']):.2f}$</b>\n\n"
        "Выберите операцию:",
        reply_markup=admin_balance_operation_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("balance_op:"))
async def callback_balance_operation(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return
    operation = callback.data.split(":", 1)[1]
    await state.update_data(operation=operation)
    await state.set_state(AdminBalanceForm.waiting_amount)
    op_text = "добавить" if operation == "add" else "вычесть"
    await callback.message.answer(
        f"Введите сумму USD для операции ({op_text}):",
        reply_markup=back_to_main_button()
    )


@router.message(AdminBalanceForm.waiting_amount)
async def admin_balance_amount_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    amount = validate_amount(message.text or "")
    if amount is None:
        await message.answer("❌ Введите корректную сумму:")
        return

    data = await state.get_data()
    target_id = data.get("target_user_id")
    operation = data.get("operation", "add")

    if operation == "subtract":
        amount = -amount

    new_balance = await db.update_balance(target_id, amount)
    await db.add_admin_log(
        f"💵 Изменение баланса: ID {target_id}, {'+' if amount >= 0 else ''}{amount}$",
        user_id=message.from_user.id
    )

    op_text = "Добавлено" if amount >= 0 else "Вычтено"
    await message.answer(
        f"✅ {op_text}: <b>{abs(amount)}$</b>\n"
        f"💰 Новый баланс: <b>{new_balance:.2f}$</b>",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await state.clear()


# ─── Balances List ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_balances_list")
async def callback_admin_balances_list(callback: CallbackQuery) -> None:
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return

    users = await db.get_all_users_balances()
    if not users:
        await callback.message.answer("📊 Список пользователей пуст.", reply_markup=admin_panel_keyboard())
        return

    now = datetime.now(timezone.utc)
    lines = ["📊 <b>Балансы пользователей:</b>\n"]
    for user in users[:50]:
        username = f"@{user['username']}" if user.get("username") else f"ID:{user['user_id']}"
        balance = float(user.get("balance", 0))
        sub_until = user.get("subscription_until")
        if sub_until:
            try:
                expiry = datetime.fromisoformat(sub_until)
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                sub_status = "✅ Активна" if expiry > now else "❌ Истекла"
            except (ValueError, TypeError):
                sub_status = "❌ Нет"
        else:
            sub_status = "❌ Нет"
        lines.append(f"{username} | {user['user_id']} | {balance:.2f}$ | {sub_status}")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n..."

    await callback.message.answer(text, reply_markup=admin_panel_keyboard(), parse_mode="HTML")


# ─── Promo Code Creation ──────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_create_promo")
async def callback_admin_create_promo(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminPromoForm.waiting_code)
    await callback.message.answer(
        "🎫 <b>Создать промокод</b>\n\nВведите код (например: <code>PROMO123</code>):",
        reply_markup=back_to_main_button(),
        parse_mode="HTML"
    )


@router.message(AdminPromoForm.waiting_code)
async def admin_promo_code_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    code = message.text.strip().upper() if message.text else ""
    if not code:
        await message.answer("❌ Введите код промокода:")
        return
    await state.update_data(promo_code=code)
    await state.set_state(AdminPromoForm.waiting_reward)
    await message.answer(f"🎫 Код: <b>{code}</b>\n\nВведите размер награды в USD:", parse_mode="HTML")


@router.message(AdminPromoForm.waiting_reward)
async def admin_promo_reward_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    reward = validate_amount(message.text or "")
    if reward is None:
        await message.answer("❌ Введите корректную сумму (например: <code>5.00</code>):", parse_mode="HTML")
        return
    await state.update_data(promo_reward=reward)
    await state.set_state(AdminPromoForm.waiting_max_activations)
    await message.answer(f"💰 Награда: <b>{reward}$</b>\n\nВведите максимальное количество активаций:", parse_mode="HTML")


@router.message(AdminPromoForm.waiting_max_activations)
async def admin_promo_max_activations_received(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    max_act = validate_positive_int(message.text or "")
    if max_act is None:
        await message.answer("❌ Введите положительное целое число:")
        return

    data = await state.get_data()
    code = data.get("promo_code", "")
    reward = float(data.get("promo_reward", 0))

    success = await db.create_promo_code(code, reward, max_act, message.from_user.id)
    if success:
        await db.add_admin_log(
            f"🎫 Создан промокод: {code}, {reward}$, {max_act} активаций",
            user_id=message.from_user.id
        )
        await message.answer(
            f"✅ <b>Промокод создан!</b>\n\n"
            f"🎫 Код: <code>{code}</code>\n"
            f"💰 Награда: <b>{reward}$</b>\n"
            f"🔢 Макс. активаций: <b>{max_act}</b>",
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ Промокод <code>{code}</code> уже существует.",
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )
    await state.clear()
