from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🛠 Модули", callback_data="modules")
    builder.button(text="🛍 Магазин", callback_data="shop")
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.button(text="ℹ️ Помощь", callback_data="help")
    builder.adjust(1)
    return builder.as_markup()


def back_to_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Вернуться в главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def subscription_keyboard(channel_username):
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Вступить в канал", url=f"https://t.me/{channel_username.lstrip('@')}")
    builder.button(text="✅ Проверить подписку", callback_data="check_subscription")
    builder.adjust(1)
    return builder.as_markup()


def modules_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Швейцария", callback_data="module_switzerland")
    builder.button(text="❌ Германия", callback_data="module_wip")
    builder.button(text="❌ Другие страны", callback_data="module_wip")
    builder.button(text="🔙 Вернуться в главное меню", callback_data="main_menu")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def shop_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📧 Email Shop", callback_data="shop_email")
    builder.button(text="📦 Цифровые товары", callback_data="shop_digital")
    builder.button(text="🔙 Вернуться в главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def profile_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Пополнить баланс", callback_data="profile_topup")
    builder.button(text="💎 Купить подписку", callback_data="profile_subscription")
    builder.button(text="🎟 Промокод", callback_data="profile_promo")
    builder.button(text="🔙 Вернуться в главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def help_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👨‍💻 Обратиться в поддержку", url="https://t.me/mensorsim")
    builder.button(text="🔙 Вернуться в главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def payment_method_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="CryptoBot", callback_data="pay_cryptobot")
    builder.button(text="xRocket", callback_data="pay_xrocket")
    builder.button(text="🔙 Вернуться в главное меню", callback_data="main_menu")
    builder.adjust(2, 1)
    return builder.as_markup()


def subscription_days_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="1 день - 6$", callback_data="sub_1")
    builder.button(text="3 дня - 12$", callback_data="sub_3")
    builder.button(text="15 дней - 28$", callback_data="sub_15")
    builder.button(text="🔙 В меню", callback_data="profile")
    builder.adjust(1)
    return builder.as_markup()


def check_payment_keyboard(invoice_id, method):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Проверить оплату", callback_data=f"check_payment:{invoice_id}:{method}")
    builder.button(text="🔙 Вернуться в главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def email_order_keyboard(order_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data=f"email_refresh:{order_id}")
    builder.button(text="♻️ Пересоздать", callback_data=f"email_reorder:{order_id}")
    builder.button(text="📩 Получить сообщение", callback_data=f"email_getmsg:{order_id}")
    builder.button(text="🔙 В меню", callback_data="shop")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🚫 Забанить", callback_data="admin_ban")
    builder.button(text="✅ Разбанить", callback_data="admin_unban")
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.button(text="📦 Управление товарами", callback_data="admin_products")
    builder.button(text="💵 Изменить баланс", callback_data="admin_balance")
    builder.button(text="📊 Список балансов", callback_data="admin_balances")
    builder.button(text="🎫 Создать промокод", callback_data="admin_promo")
    builder.button(text="🔙 Вернуться в главное меню", callback_data="main_menu")
    builder.adjust(2, 1, 1, 1, 1, 1, 1)
    return builder.as_markup()


def admin_products_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить товар", callback_data="admin_product_add")
    builder.button(text="📋 Список товаров", callback_data="admin_product_list")
    builder.button(text="🗑️ Удалить товар", callback_data="admin_product_delete")
    builder.button(text="🔙 Назад", callback_data="admin_panel")
    builder.adjust(1)
    return builder.as_markup()


def admin_broadcast_type_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Текст", callback_data="broadcast_text")
    builder.button(text="🖼️ Фото + Текст", callback_data="broadcast_photo")
    builder.button(text="🔙 Назад", callback_data="admin_panel")
    builder.adjust(2, 1)
    return builder.as_markup()


def admin_balance_operation_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить", callback_data="balance_add")
    builder.button(text="➖ Вычесть", callback_data="balance_sub")
    builder.button(text="🔙 Назад", callback_data="admin_panel")
    builder.adjust(2, 1)
    return builder.as_markup()


def products_keyboard(products):
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product['name']} [{product['stock_quantity']}]",
            callback_data=f"buy_product:{product['id']}"
        )
    builder.button(text="🔙 В меню", callback_data="shop")
    builder.adjust(1)
    return builder.as_markup()


def confirm_purchase_keyboard(product_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data=f"confirm_buy:{product_id}")
    builder.button(text="❌ Отмена", callback_data="shop_digital")
    builder.adjust(2)
    return builder.as_markup()
