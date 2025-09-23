import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from loguru import logger

from rudeai_bot.config.settings import settings
from rudeai_bot.services.ai_service import AIService
from rudeai_bot.handlers.bot_handlers import BotHandlers
from rudeai_bot.database.base import engine, Base
from rudeai_bot.utils.logger import setup_logging


class RudeAIBot:
    def __init__(self):
        self.ai_service = AIService()
        self.handlers = BotHandlers(self.ai_service)

    def setup_database(self):
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

    def setup_bot(self) -> Application:
        application = Application.builder().token(settings.telegram_bot_token).build()

        application.add_handler(CommandHandler("start", self.handlers.start_command))
        application.add_handler(CommandHandler("help", self.handlers.help_command))
        application.add_handler(CommandHandler("stats", self.handlers.stats_command))
        application.add_handler(CommandHandler("rudeness", self.handlers.rudeness_command))

        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message)
        )

        application.add_error_handler(self.handlers.error_handler)

        logger.info("Bot handlers registered successfully")
        return application

    async def run(self):
        setup_logging()
        logger.info("Starting RUDE.AI Telegram Bot...")

        self.setup_database()
        application = self.setup_bot()

        try:
            await application.initialize()
            await application.start()
            await application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )

            logger.info("Bot is running. Press Ctrl+C to stop.")

            try:
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")

        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            await self.ai_service.close()
            logger.info("Bot stopped successfully")


if __name__ == "__main__":
    bot = RudeAIBot()
    asyncio.run(bot.run())