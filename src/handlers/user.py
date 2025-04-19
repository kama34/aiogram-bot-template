from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from services.database import get_database_session, User, Referral, CartItem
from services.user_service import UserService
from keyboards.admin_kb import admin_inlin_kb
from keyboards.user_kb import user_kb
from keyboards.admin_kb import admin_reply_kb
from utils.admin_utils import is_admin
from config import ADMIN_IDS, BOT_TOKEN
from utils.subscription_utils import check_user_subscriptions
from utils.logger import setup_logger
from utils.message_utils import show_subscription_message
from services.product_service import get_product_price, get_product_name, get_product_stock
from bot import dp, bot

import re

# Setup logger for this module
logger = setup_logger('handlers.user')

# Get bot username for referral links
async def get_bot_username():
    """Get bot username for referral links with improved error handling"""
    try:
        from bot import bot
        bot_info = await bot.get_me()
        logger.info(f"Successfully retrieved bot username: {bot_info.username}")
        return bot_info.username
    except ImportError as e:
        logger.critical(f"Failed to import bot module: {e}", exc_info=True)
        return "botusername"  # Fallback name
    except Exception as e:
        logger.error(f"Failed to get bot username: {e}", exc_info=True)
        return "botusername"  # Fallback name

async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    full_name = message.from_user.full_name or "Unknown User"
    
    # Check for referral parameter
    referrer_id = None
    args = message.get_args()
    
    if args and args.startswith("ref_"):
        try:
            referrer_id = int(args.replace("ref_", ""))
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing referrer ID: {e}", exc_info=True)
            referrer_id = None
    
    try:
        with UserService() as user_service:
            # Check if user already exists
            existing_user = user_service.get_user_by_id(user_id)
            is_new_user = not existing_user
            
            # Register new user if needed
            if is_new_user:
                try:
                    new_user = User(
                        id=user_id,
                        username=username,
                        full_name=full_name
                    )
                    user_service.session.add(new_user)
                    user_service.session.commit()
                    logger.info(f"New user registered: {user_id} ({username})")
                    
                    # Process referral for new users
                    if referrer_id and referrer_id != user_id:
                        await process_referral(user_service, user_id, referrer_id, full_name, username)
                except Exception as e:
                    logger.error(f"Error registering user: {e}", exc_info=True)
                    user_service.session.rollback()
            else:
                # Process referral even for existing users who haven't been referred before
                if referrer_id and referrer_id != user_id:
                    # Check if this user already has a referrer
                    existing_referral = user_service.get_referral_by_user_id(user_id)
                    if not existing_referral:
                        await process_referral(user_service, user_id, referrer_id, full_name, username)
            
            # Show normal welcome message with appropriate keyboard based on user type
            welcome_message = "Добро пожаловать в бота!" if not is_new_user else "Добро пожаловать! Вы успешно зарегистрированы."
            
            # Choose the appropriate keyboard based on whether the user is an admin
            keyboard = admin_reply_kb if is_admin(user_id) else user_kb
            
            await message.answer(welcome_message, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Error in start_command: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке команды. Попробуйте позже.")

async def process_referral(user_service, user_id, referrer_id, full_name, username):
    """Process a referral and send notifications"""
    try:
        referrer = user_service.get_user_by_id(referrer_id)
        if not referrer:
            logger.warning(f"Referrer {referrer_id} not found when processing referral for user {user_id}")
            return
            
        # Create referral record with explicit commit
        try:
            new_referral = Referral(
                user_id=user_id,
                referred_by=referrer_id
            )
            user_service.session.add(new_referral)
            user_service.session.commit()
            logger.info(f"Referral created: user {user_id} referred by {referrer_id}")
            
            # Get bot instance for messaging
            from bot import bot
            
            # Send notification to the new user (invitee)
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"Вы были приглашены пользователем {referrer.full_name}!"
                )
            except Exception as e:
                logger.error(f"Failed to send notification to invitee {user_id}: {e}", exc_info=True)
            
            # Send notification to the referrer
            try:
                await bot.send_message(
                    chat_id=referrer_id, 
                    text=f"По вашей реферальной ссылке пришёл пользователь: {full_name} (@{username})"
                )
            except Exception as e:
                logger.error(f"Failed to send notification to referrer {referrer_id}: {e}", exc_info=True)
            
            # Notify admin about the referral
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"🔔 Новый реферал!\n\n"
                            f"Пригласил: {referrer.full_name} (@{referrer.username}, ID: {referrer.id})\n"
                            f"Приглашён: {full_name} (@{username}, ID: {user_id})"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}", exc_info=True)
                    
        except Exception as e:
            logger.error(f"Error creating referral record: {e}", exc_info=True)
            user_service.session.rollback()
    except Exception as e:
        logger.error(f"Error processing referral: {e}", exc_info=True)
        
async def referral_command(message: types.Message):
    """Generate a referral link for the user"""
    user_id = message.from_user.id
    
    # For admin users, redirect to the admin panel version
    if is_admin(user_id):
        # Create a "fake" message object that matches what admin_referral_link expects
        class AdminMessage:
            def __init__(self, chat_id):
                self.chat = types.Chat(id=chat_id, type="private")
                self.answer = message.answer
        
        admin_msg = AdminMessage(user_id)
        from handlers.admin import admin_referral_link
        await admin_referral_link(admin_msg)
        return
    
    # Regular user flow continues as before...
    bot_username = await get_bot_username()
    
    # Create a referral link with the user's ID
    # Make sure there's no space or other characters that could break the parameter
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # Get how many users this user has referred
    with UserService() as user_service:
        referral_count = user_service.count_user_referrals(user_id)
    
    # Create share buttons with cleaner formatting
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Direct link button
    keyboard.add(
        types.InlineKeyboardButton("🔗 Скопировать ссылку", callback_data=f"copy_ref_{user_id}")
    )
    
    # Share button - make sure no extra spaces or characters
    keyboard.add(
        types.InlineKeyboardButton(
            "📤 Поделиться", 
            switch_inline_query=f"Приглашаю тебя в бота! {referral_link}"
        )
    )
    
    await message.answer(
        f"🔗 <b>Ваша реферальная ссылка:</b>\n\n"
        f"<code>{referral_link}</code>\n\n"
        f"Поделитесь этой ссылкой с друзьями! Вы пригласили: <b>{referral_count}</b> пользователей",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def my_referrals_command(message: types.Message):
    """Show the user's referrals"""
    user_id = message.from_user.id
    
    with UserService() as user_service:
        referrals = user_service.get_user_referrals(user_id)
        
        if not referrals:
            # Add a button to get referral link when no referrals found
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                types.InlineKeyboardButton("🔗 Получить реферальную ссылку", callback_data=f"get_ref_link")
            )
            await message.answer("У вас пока нет приглашённых пользователей.", reply_markup=keyboard)
            return
        
        # Count total referrals
        total_referrals = len(referrals)
        
        # Build referral list with more details
        referral_text = f"👥 <b>Ваши приглашённые пользователи</b> ({total_referrals}):\n\n"
        
        for i, ref in enumerate(referrals, 1):
            user = user_service.get_user_by_id(ref.user_id)
            if user:
                date_str = ref.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(ref, 'created_at') else "неизвестно"
                username_display = f"@{user.username}" if user.username else "без username"
                referral_text += f"{i}. <b>{user.full_name}</b> ({username_display})\n   📅 {date_str}\n"
        
        # Add statistics summary
        referral_text += f"\n<b>Всего приглашено:</b> {total_referrals} пользователей"
        
        # Create keyboard with useful actions
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            types.InlineKeyboardButton("🔗 Получить реферальную ссылку", callback_data="get_ref_link")
        )
    
    await message.answer(referral_text, parse_mode="HTML", reply_markup=keyboard)

# Add handler for the get_ref_link callback
async def get_ref_link_callback(callback: types.CallbackQuery):
    """Handle the get referral link button"""
    try:
        await callback.answer()
    except Exception as e:
        logger.error(f"Error answering callback: {e}", exc_info=True)
    
    # Just call the existing referral command
    await referral_command(callback.message)

async def check_subscription_command(message: types.Message):
    with UserService() as user_service:
        user = user_service.get_user_by_id(message.from_user.id)
        if user:
            await message.answer("You are subscribed!")
        else:
            await message.answer("You are not subscribed. Please subscribe to continue.")

async def text_handler(message: types.Message):
    """Handle text messages for keyboard buttons"""
    text = message.text
    
    # Always allow help regardless of user status
    if text == "ℹ️ Помощь":
        await help_command(message)
        return
    
    # For all other commands, check if user is blocked
    with get_database_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if user and hasattr(user, 'is_blocked') and user.is_blocked:
            await message.answer("Ваш аккаунт заблокирован. Используйте кнопку 'ℹ️ Помощь' для поддержки.")
            return
    
    # Process other commands for non-blocked users
    if text == "🔍 Профиль":
        await profile_command(message)
    elif text == "🔗 Реферальная ссылка":
        await referral_command(message)
    elif text == "👥 Мои рефералы":
        await my_referrals_command(message)
    elif text == "🛒 Меню":
        await menu_command(message)
    elif text == "🧺 Корзина":
        await cart_command(message)
    elif text == "🔧 Панель администратора" and is_admin(message.from_user.id):
        from handlers.admin import admin_panel
        await admin_panel(message)

async def copy_ref_link_callback(callback: types.CallbackQuery):
    """Handle the copy referral link button with improved error handling"""
    user_id = None
    
    try:
        # Ответ на callback должен быть как можно раньше, чтобы предотвратить ожидание у пользователя
        await callback.answer("Ссылка скопирована в сообщение ниже")
    except Exception as e:
        logger.error(f"Error answering callback: {e}", exc_info=True)
    
    try:
        # Extract user ID from callback data with validation
        user_id_str = callback.data.replace("copy_ref_", "")
        
        # Строгая валидация input данных
        if not user_id_str or not user_id_str.isdigit():
            logger.warning(f"Invalid user ID format in callback data: {callback.data}")
            await callback.message.answer(
                "Ошибка: неверный формат ID пользователя. Пожалуйста, попробуйте получить ссылку заново.",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔄 Получить новую ссылку", callback_data="get_ref_link")
                )
            )
            return
            
        user_id = int(user_id_str)  # Убедимся, что это число
        
        # Generate link
        bot_username = await get_bot_username()
        if not bot_username or bot_username == "botusername":
            logger.warning(f"Using fallback bot username for user {user_id}")
            
        referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        logger.info(f"Generated referral link for user {user_id}: {referral_link}")
        
        # Send as a separate message for easy copying
        await callback.message.answer(
            f"<code>{referral_link}</code>\n\nСкопируйте эту ссылку и отправьте друзьям",
            parse_mode="HTML"
        )
    except ValueError as e:
        # Специфическая обработка ошибки преобразования типов
        logger.error(f"Value error in copy_ref_link_callback: {e}", exc_info=True)
        await callback.message.answer(
            "Произошла ошибка при создании ссылки. Некорректный формат данных."
        )
    except Exception as e:
        # Контекстная информация для логирования
        context = {
            "user_id": user_id,
            "callback_data": callback.data,
            "from_user": callback.from_user.id
        }
        logger.error(f"Error in copy_ref_link_callback: {e}. Context: {context}", exc_info=True)
        
        # Информативное сообщение для пользователя с возможностью повторить
        await callback.message.answer(
            "Произошла ошибка при создании реферальной ссылки. Пожалуйста, попробуйте позже.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔄 Попробовать снова", callback_data="get_ref_link")
            )
        )

async def profile_command(message: types.Message):
    """Show user profile information with improved error handling"""
    user_id = message.from_user.id
    
    try:
        with UserService() as user_service:
            # Get user data from database
            user = user_service.get_user_by_id(user_id)
            
            if not user:
                logger.warning(f"User profile not found for ID: {user_id}")
                await message.answer("Ошибка: Ваш профиль не найден! Пожалуйста, перезапустите бота с помощью команды /start")
                return
            
            # Get referral counts
            try:
                referral_count = user_service.count_user_referrals(user_id)
            except Exception as e:
                logger.error(f"Error getting referral count for user {user_id}: {e}", exc_info=True)
                referral_count = 0
            
            # Get referrer info if available
            referrer = None
            try:
                referral_info = user_service.get_referral_by_user_id(user_id)
                if referral_info and referral_info.referred_by:
                    referrer = user_service.get_user_by_id(referral_info.referred_by)
            except Exception as e:
                logger.error(f"Error getting referrer for user {user_id}: {e}", exc_info=True)
            
            # Format registration date safely
            try:
                registered_date = user.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(user, "created_at") and user.created_at else "неизвестно"
            except (AttributeError, ValueError) as e:
                logger.warning(f"Error formatting date for user {user_id}: {e}")
                registered_date = "неизвестно"
            
            # Build profile text
            profile_text = (
                f"👤 <b>Ваш профиль</b>\n\n"
                f"🆔 ID: <code>{user.id}</code>\n"
                f"👤 Имя: {user.full_name}\n"
                f"🔖 Username: @{user.username}\n"
                f"📅 Дата регистрации: {registered_date}\n\n"
                f"👥 Приглашено пользователей: <b>{referral_count}</b>\n"
            )
            
            # Add referrer info if available
            if referrer:
                profile_text += f"👨‍👦 Вас пригласил: {referrer.full_name} (@{referrer.username})\n"
            
            # Create keyboard with referral link button
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("🔗 Моя реферальная ссылка", callback_data="get_ref_link"))
            
            logger.info(f"Successfully generated profile for user {user_id}")
            await message.answer(profile_text, parse_mode="HTML", reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Unexpected error in profile_command for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "Произошла ошибка при загрузке профиля. Пожалуйста, попробуйте позже или свяжитесь с администратором.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
            )
        )

async def help_command(message: types.Message):
    """Show help information"""
    help_text = (
        "ℹ️ <b>Помощь по использованию бота</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Запустить бота\n"
        "/help - Показать эту справку\n"
        "/referral - Получить реферальную ссылку\n"
        "/myreferrals - Показать ваших рефералов\n\n"
        
        "<b>Как пользоваться ботом:</b>\n"
        "• Используйте <b>Профиль</b> чтобы увидеть информацию о вашем аккаунте\n"
        "• Нажмите <b>Реферальная ссылка</b> чтобы получить ссылку для приглашения друзей\n"
        "• В разделе <b>Мои рефералы</b> вы увидите список приглашённых вами пользователей\n\n"
        
        "<b>Система рефералов:</b>\n"
        "• Приглашайте друзей по вашей реферальной ссылке\n"
        "• Отслеживайте количество приглашённых пользователей\n\n"
        
        "Если у вас остались вопросы, свяжитесь с администратором."
    )
    
    await message.answer(help_text, parse_mode="HTML")

async def menu_command(message: types.Message):
    """Показывает меню с продуктами и их ценами в звездах"""
    # Создаем клавиатуру с продуктами
    products_kb = types.InlineKeyboardMarkup(row_width=2)
    
    # Добавляем товары с ценами в звездах
    for product_id in range(1, 5):
        price = get_product_price(product_id)
        products_kb.add(
            types.InlineKeyboardButton(
                f"Продукт {product_id} - {price} ⭐", 
                callback_data=f"product_{product_id}"
            )
        )
    
    await message.answer("Вы перешли в раздел меню, выберите продукт:", reply_markup=products_kb)
    
async def product_callback(callback: types.CallbackQuery):
    """Обработка выбора продукта"""
    product_id = callback.data.replace("product_", "")
    await callback.answer()
    
    try:
        # Удаляем предыдущее сообщение с меню
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Получаем цену продукта в звездах
    price = get_product_price(product_id)
    
    # Создаем клавиатуру с кнопками действий
    product_kb = types.InlineKeyboardMarkup(row_width=2)
    product_kb.add(
        types.InlineKeyboardButton("🛒 Добавить в корзину", callback_data=f"select_quantity_{product_id}")
    )
    product_kb.add(
        types.InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")
    )
    
    # Отправляем информацию о продукте с кнопками и ценой в звездах
    await callback.message.answer(
        f"Вы выбрали продукт {product_id}.\n\n"
        f"💰 Цена: {price} ⭐\n\n"
        f"Здесь будет подробная информация о продукте.",
        reply_markup=product_kb
    )

async def back_to_menu_callback(callback: types.CallbackQuery):
    """Обработка кнопки возврата в меню"""
    await callback.answer()
    
    try:
        # Удаляем сообщение с информацией о продукте
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Показываем меню снова
    products_kb = types.InlineKeyboardMarkup(row_width=2)
    
    # Добавляем товары с ценами
    for product_id in range(1, 5):
        price = get_product_price(product_id)
        products_kb.add(
            types.InlineKeyboardButton(
                f"Продукт {product_id} - {price} ₽", 
                callback_data=f"product_{product_id}"
            )
        )
    
    await callback.message.answer("Вы перешли в раздел меню, выберите продукт:", reply_markup=products_kb)

async def cart_command(message: types.Message):
    """Показывает корзину пользователя"""
    await show_cart(message, message.from_user.id)

async def view_cart_callback(callback: types.CallbackQuery):
    """Обработка кнопки просмотра корзины"""
    await callback.answer()
    
    try:
        # Удаляем предыдущее сообщение
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Показываем корзину
    await show_cart(callback.message, callback.from_user.id)

async def show_cart(message, user_id):
    """Общий метод для отображения корзины"""
    try:
        with get_database_session() as session:
            # Получаем товары из корзины пользователя
            cart_items = session.query(CartItem).filter(
                CartItem.user_id == user_id
            ).all()
            
            if not cart_items:
                # Корзина пуста
                cart_kb = types.InlineKeyboardMarkup(row_width=1)
                cart_kb.add(
                    types.InlineKeyboardButton("🛒 Перейти к товарам", callback_data="go_to_menu")
                )
                
                await message.answer(
                    "🧺 <b>Ваша корзина</b>\n\n"
                    "В данный момент ваша корзина пуста.\n"
                    "Выберите товары в нашем меню!",
                    parse_mode="HTML",
                    reply_markup=cart_kb
                )
                return
            
            # Формируем сообщение с товарами в корзине
            cart_text = "🧺 <b>Ваша корзина</b>\n\n"
            total_items = 0
            total_cost = 0
            
            for item in cart_items:
                product_name = get_product_name(item.product_id)
                price = get_product_price(item.product_id)
                item_cost = price * item.quantity
                total_items += item.quantity
                total_cost += item_cost
                cart_text += f"• {product_name} - {item.quantity} шт. × {price} ⭐ = {item_cost} ⭐\n"
            
            cart_text += f"\n<b>Всего товаров:</b> {total_items}\n"
            cart_text += f"<b>Итоговая стоимость:</b> {total_cost} ⭐"
            
            # Создаем клавиатуру для управления корзиной и удаления товаров
            cart_kb = types.InlineKeyboardMarkup(row_width=3)
            
            # Добавляем кнопки для управления каждым товаром
            for item in cart_items:
                product_name = get_product_name(item.product_id)
                # Получаем доступные остатки товара
                available_stock = get_product_stock(item.product_id)
                # Добавляем кнопки уменьшения, увеличения и удаления товара
                cart_kb.row(
                    types.InlineKeyboardButton(
                        f"➖", 
                        callback_data=f"remove_one_{item.product_id}"
                    ),
                    types.InlineKeyboardButton(
                        f"{product_name} ({item.quantity})",
                        callback_data=f"product_info_{item.product_id}"
                    ),
                    types.InlineKeyboardButton(
                        f"➕", 
                        callback_data=f"add_one_{item.product_id}"
                    )
                )
                cart_kb.row(
                    types.InlineKeyboardButton(
                        f"❌ Удалить {product_name}", 
                        callback_data=f"remove_all_{item.product_id}"
                    )
                )
            
            # Добавляем общие кнопки управления
            cart_kb.row(types.InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout"))
            cart_kb.row(types.InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart"))
            cart_kb.row(types.InlineKeyboardButton("🛒 Продолжить покупки", callback_data="go_to_menu"))
            
            await message.answer(cart_text, parse_mode="HTML", reply_markup=cart_kb)
            
    except Exception as e:
        logger.error(f"Error displaying cart for user {user_id}: {e}", exc_info=True)
        await message.answer("Произошла ошибка при загрузке корзины. Пожалуйста, попробуйте позже.")

# Обработчик для кнопки "Перейти к товарам" в корзине
async def go_to_menu_callback(callback: types.CallbackQuery):
    """Обработка кнопки перехода в меню из корзины"""
    await callback.answer()
    
    # Удаляем сообщение с корзиной
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Показываем меню с товарами
    await menu_command(callback.message)

async def add_to_cart_callback(callback: types.CallbackQuery):
    """Обработка добавления товара в корзину"""
    product_id = callback.data.replace("add_to_cart_", "")
    user_id = callback.from_user.id
    
    await callback.answer("Товар добавлен в корзину!")
    
    try:
        with get_database_session() as session:
            # Проверяем, есть ли уже товар в корзине
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                # Если товар уже в корзине, увеличиваем количество
                cart_item.quantity += 1
            else:
                # Если товара нет, добавляем новый
                new_item = CartItem(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=1
                )
                session.add(new_item)
            
            session.commit()
            logger.info(f"User {user_id} added product {product_id} to cart")
            
            # Добавляем кнопку "Перейти в корзину"
            view_cart_kb = types.InlineKeyboardMarkup()
            view_cart_kb.add(
                types.InlineKeyboardButton("🧺 Перейти в корзину", callback_data="view_cart")
            )
            view_cart_kb.add(
                types.InlineKeyboardButton("◀️ Продолжить выбор", callback_data="back_to_menu")
            )
            
            await callback.message.answer("✅ Товар успешно добавлен в корзину!", reply_markup=view_cart_kb)
            
    except Exception as e:
        logger.error(f"Error adding item to cart: {e}", exc_info=True)
        await callback.message.answer(
            "Произошла ошибка при добавлении товара в корзину. Пожалуйста, попробуйте позже."
        )

async def clear_cart_callback(callback: types.CallbackQuery):
    """Очистка корзины пользователя"""
    user_id = callback.from_user.id
    
    try:
        with get_database_session() as session:
            # Удаляем все товары из корзины пользователя
            session.query(CartItem).filter(CartItem.user_id == user_id).delete()
            session.commit()
            
        await callback.answer("Корзина очищена!")
        
        # Показываем пустую корзину
        cart_kb = types.InlineKeyboardMarkup(row_width=1)
        cart_kb.add(
            types.InlineKeyboardButton("🛒 Перейти к товарам", callback_data="go_to_menu")
        )
        
        await callback.message.edit_text(
            "🧺 <b>Ваша корзина</b>\n\n"
            "Корзина очищена!\n"
            "Выберите товары в нашем меню!",
            parse_mode="HTML",
            reply_markup=cart_kb
        )
        
    except Exception as e:
        logger.error(f"Error clearing cart for user {user_id}: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при очистке корзины")

async def select_quantity_callback(callback: types.CallbackQuery):
    """Показывает выбор количества товара"""
    product_id = callback.data.replace("select_quantity_", "")
    await callback.answer()
    
    try:
        # Удаляем предыдущее сообщение
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Создаем клавиатуру с выбором количества
    quantity_kb = types.InlineKeyboardMarkup(row_width=5)
    quantity_buttons = []
    
    for i in range(1, 6):  # Количество от 1 до 5
        quantity_buttons.append(
            types.InlineKeyboardButton(str(i), callback_data=f"add_qty_{product_id}_{i}")
        )
    
    quantity_kb.add(*quantity_buttons)
    quantity_kb.add(types.InlineKeyboardButton("◀️ Назад", callback_data=f"product_{product_id}"))
    
    await callback.message.answer(f"Выберите количество товара:", reply_markup=quantity_kb)

async def add_to_cart_with_quantity_callback(callback: types.CallbackQuery):
    """Обработка добавления товара в корзину с выбранным количеством"""
    # Парсим данные из callback_data
    parts = callback.data.replace("add_qty_", "").split("_")
    product_id = parts[0]
    quantity = int(parts[1])
    user_id = callback.from_user.id
    
    # Получаем доступное количество товара
    available_stock = get_product_stock(product_id)
    
    # Проверяем, есть ли уже товар в корзине пользователя
    current_in_cart = 0
    try:
        with get_database_session() as session:
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                current_in_cart = cart_item.quantity
    except Exception as e:
        logger.error(f"Error checking cart: {e}", exc_info=True)
    
    # Проверяем, не превышаем ли мы доступное количество
    if quantity + current_in_cart > available_stock:
        await callback.answer(f"Недостаточно товара! Доступно: {available_stock} шт.")
        return
    
    # Получаем цену продукта в звездах
    price = get_product_price(product_id)
    total_price = price * quantity
    
    await callback.answer(f"Добавлено {quantity} шт. в корзину!")
    
    try:
        # Удаляем предыдущее сообщение с выбором количества
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    try:
        with get_database_session() as session:
            # Проверяем, есть ли уже товар в корзине
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                # Если товар уже в корзине, увеличиваем количество
                cart_item.quantity += quantity
            else:
                # Если товара нет, добавляем новый
                new_item = CartItem(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity
                )
                session.add(new_item)
            
            session.commit()
            logger.info(f"User {user_id} added {quantity} of product {product_id} to cart")
            
            # Добавляем кнопку "Перейти в корзину"
            view_cart_kb = types.InlineKeyboardMarkup()
            view_cart_kb.add(
                types.InlineKeyboardButton("🧺 Перейти в корзину", callback_data="view_cart")
            )
            view_cart_kb.add(
                types.InlineKeyboardButton("◀️ Продолжить выбор", callback_data="back_to_menu")
            )
            
            await callback.message.answer(
                f"✅ В корзину добавлено: Продукт {product_id} - {quantity} шт.\n"
                f"💰 Стоимость: {total_price} ⭐", 
                reply_markup=view_cart_kb
            )
            
    except Exception as e:
        logger.error(f"Error adding item to cart: {e}", exc_info=True)
        await callback.message.answer(
            "Произошла ошибка при добавлении товара в корзину. Пожалуйста, попробуйте позже."
        )

async def remove_one_item_callback(callback: types.CallbackQuery):
    """Удаление одной единицы товара из корзины"""
    product_id = callback.data.replace("remove_one_", "")
    user_id = callback.from_user.id
    
    try:
        with get_database_session() as session:
            # Находим товар в корзине
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                if cart_item.quantity > 1:
                    # Уменьшаем количество на 1
                    cart_item.quantity -= 1
                    session.commit()
                    await callback.answer(f"Удалена 1 шт. товара из корзины")
                else:
                    # Если остался 1 товар, удаляем его полностью
                    session.delete(cart_item)
                    session.commit()
                    await callback.answer("Товар удален из корзины")
            else:
                await callback.answer("Товар не найден в корзине")
                
        # Удаляем текущее сообщение с корзиной перед обновлением
        try:
            await callback.message.delete()
        except Exception as e:
            logger.error(f"Error deleting message: {e}", exc_info=True)
            
        # Обновляем отображение корзины
        await show_cart(callback.message, user_id)
        
    except Exception as e:
        logger.error(f"Error removing item from cart: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обновлении корзины")

async def remove_all_item_callback(callback: types.CallbackQuery):
    """Удаление всех единиц конкретного товара из корзины"""
    product_id = callback.data.replace("remove_all_", "")
    user_id = callback.from_user.id
    
    try:
        with get_database_session() as session:
            # Находим и удаляем товар из корзины
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                session.delete(cart_item)
                session.commit()
                await callback.answer("Товар удален из корзины")
            else:
                await callback.answer("Товар не найден в корзине")
                
        # Удаляем текущее сообщение с корзиной перед обновлением
        try:
            await callback.message.delete()
        except Exception as e:
            logger.error(f"Error deleting message: {e}", exc_info=True)
            
        # Обновляем отображение корзины
        await show_cart(callback.message, user_id)
        
    except Exception as e:
        logger.error(f"Error removing all items from cart: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обновлении корзины")

async def add_one_item_callback(callback: types.CallbackQuery):
    """Добавление одной единицы товара в корзину"""
    product_id = callback.data.replace("add_one_", "")
    user_id = callback.from_user.id
    
    try:
        # Проверяем доступные остатки товара
        available_stock = get_product_stock(product_id)
        
        with get_database_session() as session:
            # Находим товар в корзине
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                # Проверяем, не превышаем ли мы доступное количество
                if cart_item.quantity < available_stock:
                    # Увеличиваем количество на 1
                    cart_item.quantity += 1
                    session.commit()
                    await callback.answer(f"Добавлена 1 шт. товара в корзину")
                else:
                    await callback.answer(f"Нельзя добавить больше! Доступно: {available_stock} шт.")
            else:
                await callback.answer("Товар не найден в корзине")
        
        # Удаляем текущее сообщение с корзиной перед обновлением
        try:
            await callback.message.delete()
        except Exception as e:
            logger.error(f"Error deleting message: {e}", exc_info=True)
            
        # Обновляем отображение корзины
        await show_cart(callback.message, user_id)
        
    except Exception as e:
        logger.error(f"Error adding item to cart: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обновлении корзины")

async def checkout_callback(callback: types.CallbackQuery):
    """Обработка нажатия на кнопку оформления заказа"""
    user_id = callback.from_user.id
    await callback.answer()
    
    try:
        # Удаляем предыдущее сообщение
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    try:
        from config import STAR_TO_RUB_RATE
        
        with get_database_session() as session:
            # Получаем товары из корзины пользователя
            cart_items = session.query(CartItem).filter(
                CartItem.user_id == user_id
            ).all()
            
            if not cart_items:
                # Если корзина пуста, показываем сообщение
                await callback.message.answer(
                    "🧺 Ваша корзина пуста. Добавьте товары перед оформлением заказа."
                )
                return
            
            # Формируем сообщение с подтверждением заказа
            order_text = "📝 <b>Подтверждение заказа</b>\n\n"
            total_items = 0
            total_cost = 0
            order_items = []  # Для хранения информации о товарах в заказе
            
            for item in cart_items:
                product_name = get_product_name(item.product_id)
                price = get_product_price(item.product_id)
                item_cost = price * item.quantity
                total_items += item.quantity
                total_cost += item_cost
                
                # Сохраняем информацию о товаре в заказе
                order_items.append({
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": price,
                    "name": product_name
                })
                
                order_text += f"• {product_name} - {item.quantity} шт. × {price} ⭐ = {item_cost} ⭐\n"
            
            # Итоговая сумма сразу в звездах, без конвертации
            order_text += f"\n<b>Всего товаров:</b> {total_items}\n"
            order_text += f"<b>Итоговая стоимость:</b> {total_cost} ⭐"
            
            # Сохраняем данные о заказе в контексте пользователя
            from bot import dp
            await dp.storage.set_data(user=user_id, data={
                "order_items": order_items,
                "total_cost_stars": total_cost,
                "total_items": total_items
            })
            
            # Создаем клавиатуру с кнопкой оплаты
            payment_kb = types.InlineKeyboardMarkup(row_width=1)
            payment_kb.add(
                types.InlineKeyboardButton(
                    f"⭐ Оплатить {total_cost} звезд", 
                    callback_data="pay_with_stars"
                )
            )
            payment_kb.add(
                types.InlineKeyboardButton(
                    "◀️ Вернуться в корзину", 
                    callback_data="view_cart"
                )
            )
            
            # Отправляем сообщение с подтверждением заказа
            await callback.message.answer(
                order_text,
                parse_mode="HTML",
                reply_markup=payment_kb
            )
            
    except Exception as e:
        logger.error(f"Error processing checkout for user {user_id}: {e}", exc_info=True)
        await callback.message.answer(
            "Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте позже."
        )
        
from math import ceil  # Добавьте этот импорт в начало файла

async def pay_with_stars_callback(callback: types.CallbackQuery):
    """Обработка оплаты звездами Telegram"""
    user_id = callback.from_user.id
    await callback.answer()
    
    try:
        # Получаем сохраненные данные о заказе
        from bot import dp, bot
        from config import PAYMENT_PROVIDER_TOKEN, PAYMENT_CURRENCY
        
        user_data = await dp.storage.get_data(user=user_id)
        
        if not user_data or "total_cost_stars" not in user_data:
            await callback.message.answer("Ошибка: данные заказа не найдены. Пожалуйста, попробуйте снова.")
            return
        
        order_items = user_data.get("order_items", [])
        # Цена уже в звездах, конвертировать не нужно
        total_stars = user_data.get("total_cost_stars", 0)
        
        # Проверяем доступность товаров перед оплатой
        out_of_stock_items = []
        for item in order_items:
            available_stock = get_product_stock(item["product_id"])
            if available_stock < item["quantity"]:
                out_of_stock_items.append(f"{item['name']} (доступно: {available_stock} шт.)")
        
        if out_of_stock_items:
            # Если есть товары, которых нет в наличии
            error_text = "⚠️ <b>Некоторые товары отсутствуют в нужном количестве:</b>\n\n"
            error_text += "\n".join([f"• {item}" for item in out_of_stock_items])
            error_text += "\n\nПожалуйста, вернитесь в корзину и обновите заказ."
            
            await callback.message.answer(
                error_text,
                parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🧺 Вернуться в корзину", callback_data="view_cart")
                )
            )
            return
        
        # Для звезд используем одну общую позицию вместо списка товаров
        from aiogram.types import LabeledPrice
        
        # Создаем уникальный идентификатор платежа
        import uuid
        payment_id = f"order_{user_id}_{uuid.uuid4().hex[:8]}"
        
        # Сохраняем ID платежа и конвертированную сумму в звездах
        user_data["payment_id"] = payment_id
        user_data["total_cost_stars"] = total_stars
        await dp.storage.set_data(user=user_id, data=user_data)
        
        # Отправляем счет на оплату звездами
        await bot.send_invoice(
            chat_id=user_id,
            title=f"Оплата {total_stars} ⭐",
            description=f"Пожалуйста, завершите оплату в размере {total_stars} звезд для оформления заказа.",
            payload=payment_id,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency=PAYMENT_CURRENCY,
            prices=[LabeledPrice(
                label=f"Оплата {total_stars} ⭐",
                amount=int(total_stars)
            )],
            start_parameter="stars_payment",
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False
        )
        
    except Exception as e:
        logger.error(f"Error initiating payment for user {user_id}: {e}", exc_info=True)
        await callback.message.answer(
            f"Произошла ошибка при инициализации платежа: {str(e)}. Пожалуйста, попробуйте позже."
        )

async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    """Обработка pre-checkout запроса"""
    user_id = pre_checkout_query.from_user.id
    
    try:
        # Получаем данные о заказе
        from bot import dp, bot  # Добавляем импорт бота
        user_data = await dp.storage.get_data(user=user_id)
        
        if not user_data or "payment_id" not in user_data:
            # Если данные о заказе не найдены, отклоняем платеж
            await bot.answer_pre_checkout_query(  # Используем бота для ответа
                pre_checkout_query_id=pre_checkout_query.id,
                ok=False,
                error_message="Ошибка: данные заказа не найдены. Пожалуйста, попробуйте снова."
            )
            return
        
        # Проверяем, что платеж соответствует сохраненному заказу
        if pre_checkout_query.invoice_payload != user_data["payment_id"]:
            await bot.answer_pre_checkout_query(  # Используем бота для ответа
                pre_checkout_query_id=pre_checkout_query.id,
                ok=False,
                error_message="Ошибка: несоответствие данных платежа."
            )
            return
        
        # Все проверки прошли успешно, подтверждаем pre-checkout
        await bot.answer_pre_checkout_query(  # Используем бота для ответа
            pre_checkout_query_id=pre_checkout_query.id,
            ok=True
        )
        
    except Exception as e:
        logger.error(f"Error processing pre-checkout query for user {user_id}: {e}", exc_info=True)
        await bot.answer_pre_checkout_query(  # Используем бота для ответа
            pre_checkout_query_id=pre_checkout_query.id,
            ok=False,
            error_message="Произошла ошибка при обработке платежа. Пожалуйста, попробуйте позже."
        )
        
from datetime import datetime   
async def process_successful_payment(message: types.Message):
    """Обработка успешного платежа"""
    user_id = message.from_user.id
    payment_info = message.successful_payment
    
    try:
        # Получаем данные о заказе
        from bot import dp
        user_data = await dp.storage.get_data(user=user_id)
        
        if not user_data or "order_items" not in user_data:
            logger.error(f"Order data not found for user {user_id} after payment")
            await message.answer("Платеж получен, но возникла проблема с данными заказа. Свяжитесь с поддержкой.")
            return
        
        order_items = user_data.get("order_items", [])
        total_stars = user_data.get("total_cost_stars", 0)
        order_id = None  # Создаем переменную для хранения ID заказа
        
        # Обновляем остатки товаров и создаем заказ в одной транзакции
        with get_database_session() as session:
            # Обновляем остатки товаров на складе
            for item in order_items:
                product_id = item["product_id"]
                quantity = item["quantity"]
                
                # Уменьшаем количество товара на складе
                from services.product_service import update_product_stock
                update_product_stock(product_id, -quantity)  # отрицательное значение для уменьшения
            
            # Создаем запись о заказе в базе данных
            from services.database import Order, OrderItem
            
            # Создаем заказ
            new_order = Order(
                user_id=user_id,
                total_amount=payment_info.total_amount / 100,  # переводим из сотых долей звезды
                payment_id=payment_info.telegram_payment_charge_id,
                shipping_address=f"{message.from_user.full_name}, {payment_info.order_info.phone_number if hasattr(payment_info, 'order_info') and payment_info.order_info else 'Не указан'}"
            )
            session.add(new_order)
            session.flush()  # чтобы получить ID заказа
            
            # Сохраняем ID заказа для использования вне блока with
            order_id = new_order.id
            
            # Добавляем товары в заказ
            for item in order_items:
                order_item = OrderItem(
                    order_id=order_id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item["price"]
                )
                session.add(order_item)
            
            # Очищаем корзину пользователя
            session.query(CartItem).filter(CartItem.user_id == user_id).delete()
            
            session.commit()
        
        # Отправляем сообщение о успешном заказе
        success_message = (
            "🎉 <b>Ваш заказ оформлен!</b>\n\n"
            f"Номер заказа: <code>{order_id}</code>\n"  # Используем сохраненный ID
            f"Оплачено: {total_stars} ⭐\n"
            f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            "Спасибо за покупку! Мы свяжемся с вами для уточнения деталей доставки."
        )
        
        # Создаем клавиатуру с дополнительными действиями
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🛒 Перейти в магазин", callback_data="go_to_menu")
        )
        
        await message.answer(success_message, parse_mode="HTML", reply_markup=keyboard)
        
        # Уведомляем администраторов о новом заказе
        admin_notification = (
            "🔔 <b>Новый заказ!</b>\n\n"
            f"Заказ №: <code>{order_id}</code>\n"  # Используем сохраненный ID
            f"Пользователь: {message.from_user.full_name} (@{message.from_user.username})\n"
            f"ID пользователя: {user_id}\n"
            f"Оплачено: {total_stars} ⭐\n"
            f"Товаров: {len(order_items)}\n\n"
            "Детали заказа доступны в панели администратора."
        )
        
        from config import ADMIN_IDS
        for admin_id in ADMIN_IDS:
            try:
                from bot import bot
                await bot.send_message(
                    chat_id=admin_id,
                    text=admin_notification,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id} about new order: {e}")
        
    except Exception as e:
        logger.error(f"Error processing successful payment for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "Платеж успешно обработан, но возникла ошибка при оформлении заказа. "
            "Пожалуйста, свяжитесь с поддержкой и сообщите номер платежа: "
            f"<code>{payment_info.telegram_payment_charge_id}</code>",
            parse_mode="HTML"
        )
        
def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_message_handler(help_command, commands=["help"])  # Add help command
    dp.register_message_handler(profile_command, commands=["profile"])  # Add profile command
    dp.register_message_handler(referral_command, commands=["referral", "ref"])
    dp.register_message_handler(my_referrals_command, commands=["myreferrals", "myref"])
    dp.register_message_handler(check_subscription_command, commands=["check_subscription"])
    dp.register_message_handler(text_handler, content_types=types.ContentTypes.TEXT)
    
    # Callback handlers
    dp.register_callback_query_handler(
        copy_ref_link_callback, 
        lambda c: c.data and c.data.startswith("copy_ref_")
    )
    dp.register_callback_query_handler(
        get_ref_link_callback,
        lambda c: c.data == "get_ref_link"
    )
    
    # Subscription check handler
    dp.register_callback_query_handler(
        check_subscription_callback,
        lambda c: c.data == "check_subscription"
    )
    
    # Добавляем обработчик для кнопки меню
    dp.register_message_handler(menu_command, lambda message: message.text == "🛒 Меню", state="*")
    
    # Регистрация обработчика выбора продукта
    dp.register_callback_query_handler(product_callback, lambda c: c.data.startswith("product_"))
    
    # Регистрация обработчика кнопки "Назад в меню"
    dp.register_callback_query_handler(back_to_menu_callback, lambda c: c.data == "back_to_menu")
    
    # Регистрация обработчика выбора количества товара
    dp.register_callback_query_handler(select_quantity_callback, lambda c: c.data.startswith("select_quantity_"))
    
    # Регистрация обработчика добавления в корзину с выбранным количеством
    dp.register_callback_query_handler(add_to_cart_with_quantity_callback, lambda c: c.data.startswith("add_qty_"))
    
    # Регистрация обработчика команды корзины
    dp.register_message_handler(cart_command, lambda message: message.text == "🧺 Корзина", state="*")
    
    # Регистрация обработчика кнопки "Перейти в корзину"
    dp.register_callback_query_handler(view_cart_callback, lambda c: c.data == "view_cart")
    
    # Регистрация обработчика кнопки "Очистить корзину"
    dp.register_callback_query_handler(clear_cart_callback, lambda c: c.data == "clear_cart")
    
    # Регистрация обработчика кнопки "Перейти к товарам"
    dp.register_callback_query_handler(go_to_menu_callback, lambda c: c.data == "go_to_menu")
    
    # Регистрация обработчика удаления одной единицы товара
    dp.register_callback_query_handler(remove_one_item_callback, lambda c: c.data.startswith("remove_one_"))
    
    # Регистрация обработчика удаления всех единиц товара
    dp.register_callback_query_handler(remove_all_item_callback, lambda c: c.data.startswith("remove_all_"))
    
    # Регистрация обработчика добавления одной единицы товара
    dp.register_callback_query_handler(add_one_item_callback, lambda c: c.data.startswith("add_one_"))
    
    # Регистрация обработчика оформления заказа
    dp.register_callback_query_handler(checkout_callback, lambda c: c.data == "checkout")
    
    # Регистрация обработчика оплаты звездами
    dp.register_callback_query_handler(pay_with_stars_callback, lambda c: c.data == "pay_with_stars")
    
    # Регистрация обработчиков для Telegram Payments
    dp.register_pre_checkout_query_handler(process_pre_checkout_query)
    dp.register_message_handler(process_successful_payment, content_types=types.ContentTypes.SUCCESSFUL_PAYMENT)

async def check_subscription_callback(callback: types.CallbackQuery):
    """Handle the Check Subscription button with improved error handling"""
    user_id = callback.from_user.id
    
    logger.info(f"User {user_id} initiated subscription check")
    
    # Сначала отвечаем на callback, чтобы убрать "часики" у пользователя
    try:
        await callback.answer("Проверяю статус...")
    except Exception as e:
        logger.error(f"Error answering callback for user {user_id}: {e}", exc_info=True)
    
    # Check if user is an exception first
    try:
        with get_database_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if user and hasattr(user, 'is_exception') and user.is_exception:
                logger.info(f"User {user_id} is marked as exception, bypassing subscription checks")
                
                try:
                    # User is an exception, show special message
                    await callback.message.delete()  # Delete the subscription check message
                    
                    # Send special message for exception users
                    keyboard = user_kb
                    if is_admin(user_id):
                        keyboard = admin_reply_kb
                        
                    await callback.message.answer(
                        "✨ <b>Вы являетесь исключительным пользователем!</b>\n\n"
                        "Вам не требуется подписка на каналы для использования бота.",
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                    return
                except Exception as e:
                    logger.error(f"Error handling exception user display for {user_id}: {e}", exc_info=True)
                    # Продолжаем выполнение, чтобы попробовать обычную проверку подписок
    except Exception as e:
        logger.error(f"Error checking if user {user_id} is an exception: {e}", exc_info=True)
    
    # Regular subscription check with improved error handling
    try:
        # Import bot inside the function for better dependency management
        try:
            from bot import bot
        except ImportError as e:
            logger.critical(f"Failed to import bot module: {e}", exc_info=True)
            await callback.message.answer("Критическая ошибка системы. Пожалуйста, сообщите администратору.")
            return
            
        try:
            is_subscribed, not_subscribed_channels = await check_user_subscriptions(bot, user_id)
        except Exception as e:
            logger.error(f"Error checking subscription status for user {user_id}: {e}", exc_info=True)
            await callback.message.answer(
                "Не удалось проверить статус подписки на каналы. Пожалуйста, попробуйте позже.",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔄 Попробовать снова", callback_data="check_subscription")
                )
            )
            return
        
        if not is_subscribed:
            # User is still not subscribed to all channels
            logger.info(f"User {user_id} is not subscribed to all required channels: {len(not_subscribed_channels)} channels remaining")
            await show_subscription_message(callback, not_subscribed_channels)
            return
        
        # User is subscribed to all channels, show welcome message
        logger.info(f"User {user_id} has subscribed to all required channels")
        
        try:
            # Пробуем отредактировать сообщение
            await callback.message.edit_text(
                "✅ Спасибо за подписку! Теперь вы можете пользоваться ботом.",
                reply_markup=None
            )
        except Exception as e:
            # Если не получилось отредактировать, отправляем новое
            logger.warning(f"Could not edit message for user {user_id}: {e}")
            await callback.message.answer(
                "✅ Спасибо за подписку! Теперь вы можете пользоваться ботом."
            )
        
        # Send main menu message with appropriate keyboard
        keyboard = admin_reply_kb if is_admin(user_id) else user_kb
        await callback.message.answer("Добро пожаловать в бота!", reply_markup=keyboard)
        
    except Exception as e:
        error_context = {
            "user_id": user_id,
            "callback_data": callback.data,
            "chat_id": callback.message.chat.id if callback.message else None
        }
        logger.error(f"Unexpected error in check_subscription_callback: {e}. Context: {error_context}", exc_info=True)
        
        try:
            # Информативное сообщение с возможностью повторить
            await callback.message.answer(
                "Произошла ошибка при проверке подписки. Пожалуйста, попробуйте позже.",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔄 Попробовать снова", callback_data="check_subscription")
                )
            )
        except Exception as inner_e:
            logger.error(f"Error sending error message to user {user_id}: {inner_e}", exc_info=True)
                
                        