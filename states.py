from aiogram.fsm.state import State, StatesGroup


class SMSForm(StatesGroup):
    waiting_country = State()
    waiting_phone = State()
    waiting_sender_name = State()
    waiting_message_text = State()


class MailForm(StatesGroup):
    waiting_domain = State()


class ProfileForm(StatesGroup):
    waiting_balance_amount = State()
    waiting_subscription_days = State()
    waiting_promo_code = State()
    waiting_payment_method = State()
    waiting_subscription_method = State()
    waiting_subscription_payment_method = State()


class AdminBanForm(StatesGroup):
    waiting_user_id = State()


class AdminUnbanForm(StatesGroup):
    waiting_user_id = State()


class AdminBroadcastForm(StatesGroup):
    waiting_message_type = State()
    waiting_broadcast_content = State()


class AdminProductForm(StatesGroup):
    waiting_category = State()
    waiting_name = State()
    waiting_price = State()
    waiting_file = State()


class AdminBalanceForm(StatesGroup):
    waiting_user_id = State()
    waiting_operation = State()
    waiting_amount = State()


class AdminPromoForm(StatesGroup):
    waiting_code = State()
    waiting_reward = State()
    waiting_max_activations = State()


class ShopForm(StatesGroup):
    waiting_quantity = State()
    waiting_payment_method = State()


class AdminCategoryForm(StatesGroup):
    waiting_category_name = State()
