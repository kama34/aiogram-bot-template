from aiogram import Dispatcher, types
import logging

class LoggingMiddleware:
    def __init__(self, dispatcher: Dispatcher):
        self.dispatcher = dispatcher
        self.logger = logging.getLogger(__name__)

    async def on_pre_process_update(self, update: types.Update, data: dict):
        self.logger.info(f"Received update: {update}")

    async def on_post_process_update(self, update: types.Update, result, data: dict):
        self.logger.info(f"Processed update: {update} with result: {result}")

    async def on_process_error(self, update: types.Update, error: Exception):
        self.logger.error(f"Error occurred: {error} for update: {update}")

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')