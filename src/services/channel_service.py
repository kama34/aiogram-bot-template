from sqlalchemy.orm import Session
from .database import Channel, get_database_session
from typing import List, Optional

class ChannelService:
    def __init__(self):
        self.session: Session = get_database_session()
    
    def add_channel(self, channel_name: str, channel_id: str) -> Channel:
        """Add a new channel to the database"""
        # Check if channel already exists
        existing_channel = self.get_channel_by_id(channel_id)
        if existing_channel:
            return existing_channel
            
        # Create new channel entry
        new_channel = Channel(
            channel_name=channel_name,
            channel_id=channel_id,
            is_enabled=True
        )
        self.session.add(new_channel)
        self.session.commit()
        return new_channel
    
    def get_channel_by_id(self, channel_id: str) -> Optional[Channel]:
        """Get channel by its Telegram ID"""
        return self.session.query(Channel).filter(Channel.channel_id == channel_id).first()
    
    def get_channel_by_id_db(self, db_id: int) -> Optional[Channel]:
        """Get channel by its database ID"""
        return self.session.query(Channel).filter(Channel.id == db_id).first()
    
    def get_all_channels(self) -> List[Channel]:
        """Get all channels"""
        return self.session.query(Channel).all()
    
    def get_enabled_channels(self) -> List[Channel]:
        """Get only enabled channels"""
        return self.session.query(Channel).filter(Channel.is_enabled == True).all()
    
    def toggle_channel(self, channel_id: str) -> Optional[Channel]:
        """Toggle channel enabled status"""
        channel = self.get_channel_by_id(channel_id)
        if channel:
            channel.is_enabled = not channel.is_enabled
            self.session.commit()
        return channel
    
    def toggle_channel_by_id(self, db_id: int) -> Optional[Channel]:
        """Toggle channel enabled status using database ID"""
        channel = self.get_channel_by_id_db(db_id)
        if channel:
            channel.is_enabled = not channel.is_enabled
            self.session.commit()
        return channel
    
    def delete_channel(self, channel_id: str) -> bool:
        """Delete a channel from the database"""
        channel = self.get_channel_by_id(channel_id)
        if channel:
            self.session.delete(channel)
            self.session.commit()
            return True
        return False
    
    def delete_channel_by_id(self, db_id: int) -> bool:
        """Delete a channel using its database ID"""
        channel = self.get_channel_by_id_db(db_id)
        if channel:
            self.session.delete(channel)
            self.session.commit()
            return True
        return False
    
    def close_session(self):
        """Close database session"""
        self.session.close()