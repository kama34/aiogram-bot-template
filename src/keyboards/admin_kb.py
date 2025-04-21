from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# Admin panel keyboard
admin_inlin_kb = InlineKeyboardMarkup(row_width=2)
admin_inlin_kb.add(
    InlineKeyboardButton("📊 Статистика", callback_data="user_stats"),
    InlineKeyboardButton("📁 Экспорт", callback_data="export_users")
)
admin_inlin_kb.add(
    InlineKeyboardButton("🔍 Пользователи", callback_data="search_user"),
    InlineKeyboardButton("📨 Рассылка", callback_data="mass_message"),
)
admin_inlin_kb.add(
    InlineKeyboardButton("📢 Каналы", callback_data="manage_channels"),
    InlineKeyboardButton("👥 Рефералка", callback_data="referral_stats"),
)
admin_inlin_kb.add(
    InlineKeyboardButton("🔗 Пригласительная ссылка", callback_data="admin_ref_link"),
    InlineKeyboardButton("🛒 Товары", callback_data="manage_products")
)

# Admin-specific keyboard with admin panel button
admin_reply_kb = ReplyKeyboardMarkup(resize_keyboard=True)
admin_reply_kb.add(KeyboardButton("🔧 Панель администратора"))