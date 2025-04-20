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