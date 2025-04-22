from aiogram import types
from services.database import Referral
from utils.logger import setup_logger
from config import ADMIN_IDS

# Setup logger for this module
logger = setup_logger('handlers.referral.utils')

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