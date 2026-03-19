from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def back_to_main_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])


def subscription_keyboard(channel_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📢 Вступить в канал",
            url=f"https://t.me/{channel_username.lstrip('@')}"
        )],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")]
    ])


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛠 Модули", callback_data="menu_modules"),
            InlineKeyboardButton(text="🛍 Магазин", callback_data="menu_shop")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile"),
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="menu_help")
        ]
    ])


def modules_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 SMS", callback_data="module_sms")],
        [InlineKeyboardButton(text="📧 Mailer", callback_data="module_mailer")],
        [InlineKeyboardButton(text="🖥 Screen", callback_data="module_screen")],
        [InlineKeyboardButton(text="🔒 Proxy", callback_data="module_proxy")],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])


def sms_country_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Швейцария", callback_data="sms_country_switzerland")],
        [InlineKeyboardButton(text="❌ Германия (Временно недоступно)", callback_data="sms_country_unavailable")],
        [InlineKeyboardButton(text="❌ Другие страны (Временно недоступно)", callback_data="sms_country_unavailable")],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])


def shop_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📧 Email Shop", callback_data="shop_email")],
        [InlineKeyboardButton(text="🛒 Цифровые товары", callback_data="shop_digital")],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])


def email_shop_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="email_refresh"),
            InlineKeyboardButton(text="♻️ Пересоздать", callback_data="email_recreate")
        ],
        [InlineKeyboardButton(text="📩 Получить сообщение", callback_data="email_get_message")],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])


def digital_products_keyboard(products: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        name = product["name"]
        stock = product["stock_quantity"]
        builder.button(
            text=f"{name} [{stock}]",
            callback_data=f"buy_product:{name}:{product['category']}"
        )
    builder.button(text="🔙 Вернуться в главное меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="profile_topup")],
        [InlineKeyboardButton(text="💎 Купить подписку", callback_data="profile_subscription")],
        [InlineKeyboardButton(text="🎟 Промокод", callback_data="profile_promo")],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])


def payment_method_keyboard(context: str = "topup") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 CryptoBot", callback_data=f"pay_cryptobot:{context}")],
        [InlineKeyboardButton(text="🚀 xRocket", callback_data=f"pay_xrocket:{context}")],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])


def subscription_plans_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день — 6$", callback_data="sub_plan:1:6.0")],
        [InlineKeyboardButton(text="3 дня — 12$", callback_data="sub_plan:3:12.0")],
        [InlineKeyboardButton(text="15 дней — 28$", callback_data="sub_plan:15:28.0")],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])


def subscription_payment_method_keyboard(days: int, price: float) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
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


def check_payment_keyboard(invoice_id: str, payment_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔄 Проверить оплату",
            callback_data=f"check_payment:{payment_type}:{invoice_id}"
        )],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])


def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Обратиться в поддержку", url="https://t.me/mensorsim")],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚫 Забанить", callback_data="admin_ban"),
            InlineKeyboardButton(text="✅ Разбанить", callback_data="admin_unban")
        ],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📦 Управление товарами", callback_data="admin_products")],
        [InlineKeyboardButton(text="💵 Изменить баланс", callback_data="admin_balance")],
        [InlineKeyboardButton(text="📊 Список балансов", callback_data="admin_balances_list")],
        [InlineKeyboardButton(text="🎫 Создать промокод", callback_data="admin_create_promo")]
    ])


def admin_products_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])


def admin_balance_operation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data="balance_op:add"),
            InlineKeyboardButton(text="➖ Вычесть", callback_data="balance_op:subtract")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])


def broadcast_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Текст", callback_data="broadcast_type:text")],
        [InlineKeyboardButton(text="🖼 Фото + текст", callback_data="broadcast_type:photo")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])


def quantity_keyboard(max_qty: int, product_name: str, category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, min(max_qty + 1, 6)):
        builder.button(text=str(i), callback_data=f"qty:{i}:{product_name}:{category}")
    builder.button(text="🔙 Вернуться в главное меню", callback_data="back_to_main")
    builder.adjust(5, 1)
    return builder.as_markup()


def confirm_sms_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="sms_confirm_send"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_main")
        ]
    ])
