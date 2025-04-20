from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.admin_utils import is_admin
from keyboards.admin_kb import admin_inlin_kb

# Состояния для операций админа
class AdminStates(StatesGroup):
    waiting_for_search = State()
    waiting_for_block_username = State()
    waiting_for_unblock_username = State()
    waiting_for_mass_message = State()
    browsing_letters = State()
    browsing_users_by_letter = State()
    waiting_for_channel_input = State()

async def admin_panel(message: types.Message):
    """Основная функция для отображения админ-панели"""
    if is_admin(message.from_user.id):
        await message.answer("Панель администратора:", reply_markup=admin_inlin_kb)
    else:
        await message.answer("У вас нет прав доступа к панели администратора.")

async def admin_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    """Главный обработчик callback-запросов для админ-панели"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    # Отвечаем на callback немедленно, чтобы избежать ошибок таймаута
    try:
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")
    
    # Сохраняем оригинальное сообщение для последующего удаления
    orig_message = callback.message
    
    # Обработка различных callback_data для админ-панели
    if callback.data == "user_stats":
        await orig_message.delete()
        from .statistics import view_user_statistics
        await view_user_statistics(orig_message)
    elif callback.data == "export_users":
        await orig_message.delete()
        from .statistics import export_user_list
        await export_user_list(orig_message)
    elif callback.data == "search_user":
        await orig_message.delete()
        # Показываем варианты поиска: по тексту или по букве
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🔍 Поиск по имени/ID", callback_data="text_search"),
            types.InlineKeyboardButton("🔤 Поиск по букве", callback_data="letter_search")
        )
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        await orig_message.answer("Выберите метод поиска пользователя:", reply_markup=keyboard)
    elif callback.data == "block_user":
        await orig_message.delete()
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="cancel_state"))
        await orig_message.answer("Введите имя пользователя (username) для блокировки:", reply_markup=keyboard)
        await AdminStates.waiting_for_block_username.set()
    elif callback.data == "unblock_user":
        await orig_message.delete()
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="cancel_state"))
        await orig_message.answer("Введите имя пользователя (username) для разблокировки:", reply_markup=keyboard)
        await AdminStates.waiting_for_unblock_username.set()
    elif callback.data == "mass_message":
        await orig_message.delete()
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="cancel_state"))
        await orig_message.answer("Введите сообщение для массовой рассылки:", reply_markup=keyboard)
        await AdminStates.waiting_for_mass_message.set()
    elif callback.data == "manage_channels":
        await orig_message.delete()
        from .channels import manage_channels_menu
        await manage_channels_menu(orig_message)
    elif callback.data == "referral_stats":
        await orig_message.delete()
        from .statistics import view_referral_statistics
        await view_referral_statistics(orig_message)
    elif callback.data == "admin_ref_link":
        await orig_message.delete()
        from .statistics import admin_referral_link
        await admin_referral_link(orig_message)
    elif callback.data == "admin_my_refs":
        await orig_message.delete()
        from .statistics import admin_my_referrals
        await admin_my_referrals(orig_message)
    elif callback.data == "admin_back":
        await orig_message.delete()
        await orig_message.answer("Панель администратора:", reply_markup=admin_inlin_kb)
    elif callback.data == "cancel_state":
        current_state = await state.get_state()
        if current_state:
            await state.finish()
        await orig_message.delete()
        await orig_message.answer("Действие отменено.", reply_markup=admin_inlin_kb)
    elif callback.data == "text_search":
        from .user_management import text_search_handler
        await text_search_handler(callback, state)
    elif callback.data == "letter_search":
        from .user_management import letter_search_handler
        await letter_search_handler(callback, state)

def register_admin_handlers(dp: Dispatcher):
    """Регистрирует обработчики для основных админ-функций"""
    dp.register_message_handler(admin_panel, commands=["admin"])
    dp.register_callback_query_handler(admin_callback_handler, lambda c: c.data.startswith(("admin_", "cancel_", "user_stats", "export_users", "search_user", "block_user", "unblock_user", "mass_message", "manage_channels", "referral_stats", "text_search", "letter_search")))