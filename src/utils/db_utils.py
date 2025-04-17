from services.database import get_database_session
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def with_session(func):
    """Decorator to provide database session to functions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        session = get_database_session()
        try:
            return await func(session=session, *args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {e}", exc_info=True)
            raise
        finally:
            session.close()
    return wrapper