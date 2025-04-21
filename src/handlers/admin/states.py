from aiogram.dispatcher.filters.state import State, StatesGroup

# Состояния для операций админа
class AdminStates(StatesGroup):
    waiting_for_search = State()
    waiting_for_block_username = State()
    waiting_for_unblock_username = State()
    waiting_for_mass_message = State()
    browsing_letters = State()
    browsing_users_by_letter = State()
    waiting_for_channel_input = State()
    
    # Состояния для управления товарами
    waiting_for_product_name = State()
    waiting_for_product_description = State()
    waiting_for_product_price = State()
    waiting_for_product_image = State()
    waiting_for_product_category = State()
    waiting_for_product_stock = State()
    product_creation_confirmation = State()
    product_editing = State()
    waiting_for_edit_field = State()
    waiting_for_edited_value = State()
    waiting_for_product_selection = State()