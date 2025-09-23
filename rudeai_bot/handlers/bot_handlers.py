from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from rudeai_bot.services.ai_service import AIService
from rudeai_bot.database.base import get_db
from rudeai_bot.database.operations import DatabaseOperations


class BotHandlers:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user

        with next(get_db()) as db:
            db_ops = DatabaseOperations(db)
            db_ops.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )

        welcome_message = (
            "Welcome to RUDE.AI! 🤖\n\n"
            "I'm your brutal productivity drill sergeant. Send me your procrastination problems "
            "and I'll give you the harsh motivation you need.\n\n"
            "No excuses. No sympathy. Just results."
        )

        await update.message.reply_text(welcome_message)
        logger.info(f"User {user.id} started the bot")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        help_text = (
            "RUDE.AI Commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/stats - View your conversation statistics\n"
            "/rudeness [1-10] - Adjust rudeness intensity level\n\n"
            "Just send me any message about what you're avoiding or procrastinating on, "
            "and I'll give you the motivation you need to get it done!\n\n"
            "Rudeness Levels:\n"
            "1-3: Sharp but not brutal\n"
            "4-6: Standard drill sergeant mode\n"
            "7-10: Maximum savage mode"
        )

        await update.message.reply_text(help_text)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user

        with next(get_db()) as db:
            db_ops = DatabaseOperations(db)
            user_obj = db_ops.get_or_create_user(telegram_id=user.id)
            conversations = db_ops.get_user_conversations(user_obj.id)

            stats_text = (
                f"📊 Your RUDE.AI Stats:\n\n"
                f"Rudeness Level: {user_obj.rudeness_level}/10\n"
                f"Total interactions: {user_obj.interaction_count}\n"
                f"Excuse count: {user_obj.excuse_count}\n"
                f"Total conversations: {len(conversations)}\n"
                f"Member since: {user_obj.created_at.strftime('%Y-%m-%d')}\n\n"
                "Keep pushing yourself! 💪"
            )

        await update.message.reply_text(stats_text)

    async def rudeness_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user

        if not context.args:
            await update.message.reply_text(
                "Usage: /rudeness [1-10]\n\n"
                "1-3: Sharp but not brutal\n"
                "4-6: Standard drill sergeant mode\n"
                "7-10: Maximum savage mode\n\n"
                "Use /stats to see your current level."
            )
            return

        try:
            level = int(context.args[0])
            if not 1 <= level <= 10:
                raise ValueError()

            with next(get_db()) as db:
                db_ops = DatabaseOperations(db)
                user_obj = db_ops.get_or_create_user(telegram_id=user.id)
                db_ops.update_user_rudeness_level(user_obj.id, level)

            level_descriptions = {
                1: "Sharp guidance", 2: "Mild impatience", 3: "Clear frustration",
                4: "Harsh disdain", 5: "Drill sergeant mode", 6: "Brutal contempt",
                7: "Zero tolerance", 8: "Savage mockery", 9: "Maximum brutality", 10: "Nuclear option"
            }

            await update.message.reply_text(
                f"Rudeness level set to {level}/10: {level_descriptions[level]}\n"
                "Brace yourself accordingly."
            )

        except (ValueError, IndexError):
            await update.message.reply_text(
                "Invalid level. Use a number between 1 and 10."
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        user_message = update.message.text

        if not user_message:
            await update.message.reply_text("Send me text, not files or stickers.")
            return

        logger.info(f"Received message from user {user.id}: {user_message[:50]}...")

        try:
            with next(get_db()) as db:
                db_ops = DatabaseOperations(db)
                user_obj = db_ops.get_or_create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )

                db_ops.increment_user_interaction(user_obj.id)

                if self.ai_service.is_excuse_message(user_message):
                    db_ops.increment_user_excuses(user_obj.id)

                recent_conversations = db_ops.get_user_conversations(user_obj.id, limit=5)
                recent_messages = [conv.user_message for conv in recent_conversations]

                user_obj = db_ops.get_user_by_telegram_id(user.id)

            ai_response = await self.ai_service.generate_response(
                user_message,
                rudeness_level=user_obj.rudeness_level,
                excuse_count=user_obj.excuse_count,
                recent_conversations=recent_messages
            )

            if ai_response:
                with next(get_db()) as db:
                    db_ops = DatabaseOperations(db)
                    db_ops.save_conversation(user_obj.id, user_message, ai_response)

                await update.message.reply_text(ai_response)
                logger.info(f"Sent response to user {user.id}")
            else:
                await update.message.reply_text(
                    "I'm temporarily overwhelmed. Try again in a moment, weakling."
                )

        except Exception as e:
            logger.error(f"Error handling message from user {user.id}: {e}")
            await update.message.reply_text(
                "Something went wrong. Even I have limits, apparently."
            )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(f"Exception while handling an update: {context.error}")

        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "An error occurred. My circuits are too advanced for this nonsense."
                )
            except Exception:
                pass