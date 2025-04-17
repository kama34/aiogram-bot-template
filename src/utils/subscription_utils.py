from services.channel_service import ChannelService

async def check_user_subscriptions(bot, user_id):
    """Check if user is subscribed to all required channels"""
    
    # Get all enabled channels
    channel_service = ChannelService()
    enabled_channels = channel_service.get_enabled_channels()
    
    # If there are no enabled channels, user is considered subscribed
    if not enabled_channels:
        channel_service.close_session()
        return True, []
    
    # Check subscription for each channel
    not_subscribed = []
    
    for channel in enabled_channels:
        try:
            member = await bot.get_chat_member(channel.channel_id, user_id)
            is_member = member.status in ['member', 'administrator', 'creator']
            
            if not is_member:
                channel_info = await bot.get_chat(channel.channel_id)
                channel_name = channel.channel_name or channel_info.title
                invite_link = channel_info.invite_link or f"https://t.me/{channel_info.username}" if channel_info.username else None
                
                not_subscribed.append({
                    'id': channel.channel_id,
                    'name': channel_name,
                    'link': invite_link
                })
        except Exception as e:
            print(f"Error checking subscription for channel {channel.channel_id}: {e}")
    
    channel_service.close_session()
    return len(not_subscribed) == 0, not_subscribed