from aiogram import types
from utils.message_utils import safe_delete_message

class MessageTracker:
    """
    Класс для отслеживания и управления сообщениями в рамках диалога
    """
    
    @staticmethod
    async def add_message_to_state(state, message, key="messages_to_delete"):
        """
        Добавляет сообщение в список для удаления в state
        """
        async with state.proxy() as data:
            if key not in data:
                data[key] = []
            
            # Добавляем информацию о сообщении
            data[key].append({
                "chat_id": message.chat.id,
                "message_id": message.message_id
            })
    
    @staticmethod
    async def delete_messages(state, key="messages_to_delete"):
        """
        Удаляет все сообщения, сохраненные в state
        """
        messages_to_delete = []
        
        # Извлекаем список сообщений
        async with state.proxy() as data:
            if key in data:
                messages_to_delete = data[key].copy()
                data[key] = []  # Очищаем список
        
        # Удаляем сообщения
        for msg_info in messages_to_delete:
            try:
                await types.bot.Bot.get_current().delete_message(
                    msg_info["chat_id"], 
                    msg_info["message_id"]
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение {msg_info['message_id']}: {e}")
                
    @staticmethod
    async def send_and_track(state, chat_id, text, reply_markup=None, parse_mode=None, key="messages_to_delete"):
        """
        Отправляет сообщение и добавляет его в список для удаления
        """
        bot = types.bot.Bot.get_current()
        message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        
        # Добавляем сообщение в список для удаления
        async with state.proxy() as data:
            if key not in data:
                data[key] = []
            
            data[key].append({
                "chat_id": message.chat.id,
                "message_id": message.message_id
            })
        
        return message