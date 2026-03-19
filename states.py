from aiogram.fsm.state import State, StatesGroup

class SMSForm(StatesGroup):
    waiting_phone = State()
    waiting_sender_name = State()
    waiting_message_text = State()

class MailForm(StatesGroup):
    waiting_domain = State()

class ProfileForm(StatesGroup):
    waiting_payment_method = State()
    waiting_balance_amount = State()
    waiting_subscription_days = State()
    waiting_promo_code = State()

class AdminForm(StatesGroup):
    waiting_ban_user_id = State()
    waiting_unban_user_id = State()
    waiting_broadcast_type = State()
    waiting_broadcast_content = State()
    waiting_broadcast_photo = State()
    waiting_broadcast_caption = State()
    waiting_product_category = State()
    waiting_product_name = State()
    waiting_product_price = State()
    waiting_product_file = State()
    waiting_product_more = State()
    waiting_delete_product_id = State()
    waiting_balance_user_id = State()
    waiting_balance_operation = State()
    waiting_balance_amount = State()
    waiting_promo_code = State()
    waiting_promo_reward = State()
    waiting_promo_max_activations = State()
