import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from loguru import logger

from rudeai_bot.config.settings import settings
from rudeai_bot.services.ai_service import AIService
from rudeai_bot.services.scheduler_service import TaskSchedulerService
from rudeai_bot.handlers.bot_handlers import BotHandlers
from rudeai_bot.database.base import engine, Base
from rudeai_bot.utils.logger import setup_logging


class RudeAIBot:
    def __init__(self):
        self.ai_service = AIService()
        self.handlers = BotHandlers(self.ai_service)
        self.scheduler = None  # Initialized in setup_bot()

    def setup_database(self):
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

    def setup_bot(self) -> Application:
        application = Application.builder().token(settings.telegram_bot_token).build()

        # Initialize scheduler with bot instance
        logger.info("🔧 Initializing TaskSchedulerService...")
        self.scheduler = TaskSchedulerService(application.bot)
        self.handlers.set_scheduler(self.scheduler)
        logger.info("✅ Scheduler connected to handlers")

        # Task creation conversation handler
        task_conversation = ConversationHandler(
            entry_points=[CommandHandler("new", self.handlers.new_task_command)],
            states={
                self.handlers.TASK_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.task_name_received)
                ],
                self.handlers.TASK_HATE_LEVEL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.task_hate_level_received)
                ],
                self.handlers.TASK_PRIORITY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.task_priority_received)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.handlers.cancel_task_creation)],
            name="task_creation",
            persistent=False,
        )

        application.add_handler(task_conversation)

        # Task completion conversation handler
        done_conversation = ConversationHandler(
            entry_points=[CommandHandler("done", self.handlers.done_command)],
            states={
                self.handlers.TASK_SELECTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.task_selection_received)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.handlers.cancel_task_completion)],
            name="task_completion",
            persistent=False,
        )

        application.add_handler(done_conversation)

        # Regular command handlers
        application.add_handler(CommandHandler("start", self.handlers.start_command))
        application.add_handler(CommandHandler("help", self.handlers.help_command))
        application.add_handler(CommandHandler("list", self.handlers.list_tasks_command))
        application.add_handler(CommandHandler("stats", self.handlers.stats_command))
        application.add_handler(CommandHandler("rudeness", self.handlers.rudeness_command))

        # Message handler (must be last)
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

            # Start scheduler and reschedule all active tasks
            logger.info("🚀 Starting task scheduler...")
            self.scheduler.start()
            logger.info("♻️ Rescheduling all active tasks...")
            await self.scheduler.reschedule_all_active_tasks()

            logger.info("✅ Bot is running. Press Ctrl+C to stop.")

            try:
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")

        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
        finally:
            # Shutdown scheduler gracefully
            if self.scheduler:
                self.scheduler.shutdown()

            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            await self.ai_service.close()
            logger.info("Bot stopped successfully")


if __name__ == "__main__":
    bot = RudeAIBot()
    asyncio.run(bot.run())