from aiogram import types
from services.product_service import get_product_by_id
from utils.logger import setup_logger

# Setup logger
logger = setup_logger('handlers.user.cart.keyboards')

def get_after_add_keyboard(product_id):
    """Возвращает клавиатуру после добавления товара в корзину"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("🛒 Перейти в корзину", callback_data="view_cart"),
        types.InlineKeyboardButton("🔍 Продолжить покупки", callback_data="back_to_categories"),
        types.InlineKeyboardButton("📦 Показать товар", callback_data=f"product_{product_id}")
    )
    return keyboard

def create_cart_keyboard(valid_items):
    """Создает клавиатуру для отображения товаров в корзине"""
    cart_kb = types.InlineKeyboardMarkup(row_width=3)
    
    # Добавляем кнопки для каждого товара
    for item in valid_items:
        try:
            product_id = item.product_id
            if isinstance(product_id, str) and product_id.isdigit():
                product_id = int(product_id)
            
            product = get_product_by_id(product_id)
            product_name = product['name'] if product else f"Товар {item.product_id}"
            
            # Добавляем кнопки управления количеством товара
            cart_kb.row(
                types.InlineKeyboardButton(
                    f"➖", 
                    callback_data=f"remove_one_{product_id}"
                ),
                types.InlineKeyboardButton(
                    f"{product_name} ({item.quantity})",
                    callback_data=f"product_{product_id}"
                ),
                types.InlineKeyboardButton(
                    f"➕", 
                    callback_data=f"add_one_{product_id}"
                )
            )
            cart_kb.row(
                types.InlineKeyboardButton(
                    f"❌ Удалить {product_name}", 
                    callback_data=f"remove_all_{product_id}"
                )
            )
        except Exception as e:
            logger.error(f"Error creating button for cart item: {e}", exc_info=True)
    
    # Добавляем общие кнопки управления корзиной
    cart_kb.row(types.InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout"))
    cart_kb.row(types.InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart"))
    cart_kb.row(types.InlineKeyboardButton("🛍️ Продолжить покупки", callback_data="back_to_categories"))
    
    return cart_kb