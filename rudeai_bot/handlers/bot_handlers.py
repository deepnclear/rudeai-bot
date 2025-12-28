from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger

from rudeai_bot.services.ai_service import AIService, AIHarassmentService
from rudeai_bot.database.base import get_db_context
from rudeai_bot.database.operations import DatabaseOperations
from rudeai_bot.handlers.messages import TaskCreationMessages


class BotHandlers:
    # Conversation states for /new and /done commands
    TASK_NAME, TASK_HATE_LEVEL, TASK_PRIORITY, TASK_SELECTION = range(4)

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.ai_harassment_service = AIHarassmentService()  # For completion messages
        self.scheduler = None  # Set later via set_scheduler()

    def set_scheduler(self, scheduler):
        """Set the scheduler service"""
        self.scheduler = scheduler

    def _format_time_ago(self, created_at) -> str:
        """Format time since task creation in a readable way"""
        from datetime import datetime, timezone

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        delta = now - created_at

        seconds = delta.total_seconds()

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"

    def _format_duration(self, seconds: float) -> str:
        """Format duration in a readable way"""
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = seconds / 3600
            if hours < 2:
                return f"{hours:.1f} hours"
            return f"{int(hours)} hours"
        else:
            days = seconds / 86400
            if days < 2:
                return f"{days:.1f} days"
            return f"{int(days)} days"

    def _get_completion_response(self, task_name: str, duration_seconds: float, hate_level: int, priority: int, reminder_count: int = 0) -> str:
        """
        Generate completion acknowledgment using AI with fallback to static messages.

        Varies based on completion speed, hate level, priority, and reminder count.

        Args:
            task_name: Name of the completed task
            duration_seconds: Time taken to complete (seconds)
            hate_level: How much the user hated this task (1-5)
            priority: Task urgency (1-5)
            reminder_count: Number of harassment messages sent (0+)
        """
        import random

        duration_str = self._format_duration(duration_seconds)

        # Determine completion speed category (5 levels for granularity)
        if duration_seconds < 900:  # Under 15 minutes
            completion_speed = "blazing"
        elif duration_seconds < 1800:  # 15-30 minutes
            completion_speed = "fast"
        elif duration_seconds < 7200:  # 30 min - 2 hours
            completion_speed = "normal"
        elif duration_seconds < 14400:  # 2-4 hours
            completion_speed = "slow"
        else:  # 4+ hours
            completion_speed = "glacial"

        # Try AI generation first
        if self.ai_harassment_service.enabled:
            ai_message = self.ai_harassment_service.generate_completion_message(
                task_name=task_name,
                time_taken=duration_str,
                hate_level=hate_level,
                priority=priority,
                completion_speed=completion_speed,
                reminder_count=reminder_count
            )

            if ai_message:
                logger.debug(f"✨ Using AI-generated completion message (speed={completion_speed}, hate={hate_level}, priority={priority}, reminders={reminder_count})")
                return ai_message

        # Fallback to static messages
        logger.debug(f"📝 Using static completion message (speed={completion_speed})")

        # BLAZING completion (<15 min)
        if completion_speed == "blazing":
            responses = [
                f"Done in {duration_str}. Blazing fast. The task you dreaded took less than a coffee break.",
                f"{duration_str}. That thing you avoided all day? Took minutes. Fear is expensive.",
                f"Completed in {duration_str}. You could've done this hours ago. You knew that.",
                f"{duration_str}. Quick work. Almost like the dread was the only hard part.",
                f"Done. {duration_str}. Turns out the task wasn't the problem. Starting was.",
            ]

        # FAST completion (15-30 min)
        elif completion_speed == "fast":
            responses = [
                f"Done. {duration_str}. That's... actually impressive. Don't let it go to your head.",
                f"{duration_str}. Faster than expected. Who are you and what did you do with the procrastinator?",
                f"Completed in {duration_str}. See? It wasn't that hard. It never is. You knew that.",
                f"{duration_str}. Quick work. Almost like you knew how to do it all along.",
                f"Done in {duration_str}. Turns out starting is the hard part. Who knew.",
            ]

        # NORMAL completion (30 min - 2 hours)
        elif completion_speed == "normal":
            responses = [
                f"Done. {duration_str}. Not a record, but you finished. That's more than most days.",
                f"'{task_name}' complete. {duration_str}. Adequate. The word you're looking for is adequate.",
                f"Finished in {duration_str}. You did the thing you said you'd do. Revolutionary concept.",
                f"{duration_str} to complete. Not fast, not slow. Perfectly mediocre.",
                f"Done. {duration_str}. A solid demonstration of doing the bare minimum required.",
            ]

        # SLOW completion (2-4 hours)
        elif completion_speed == "slow":
            responses = [
                f"{duration_str} for '{task_name}'. The task took 20 minutes. The rest was avoidance.",
                f"Done in {duration_str}. Not fast. Not efficient. But done.",
                f"Completed after {duration_str}. You made a simple task complicated. Congratulations.",
                f"{duration_str}. That's not procrastination, that's a commitment to delay.",
                f"Done. {duration_str}. The scenic route to completion. Very scenic.",
            ]

        # GLACIAL completion (4+ hours)
        else:  # glacial
            responses = [
                f"{duration_str} for '{task_name}'. You really savored the avoidance on this one.",
                f"Done. Only took {duration_str}. I've seen glaciers move faster, but sure, celebrate.",
                f"Completed after {duration_str}. The task took 20 minutes. The rest was... what, exactly?",
                f"{duration_str}. That's not procrastination, that's a lifestyle choice.",
                f"Done in {duration_str}. You stretched a simple task into an endurance event. Impressive, wrong, but impressive.",
            ]

        response = random.choice(responses)

        # Add extra acknowledgment for HIGH HATE tasks (4-5)
        if hate_level >= 4:
            hate_additions = [
                f" You actually did '{task_name}'. The thing you said you'd rather eat glass than do. Look at you, proving yourself wrong.",
                f" '{task_name}' - done. That one was sitting in your chest, wasn't it? Gone now.",
                f" You hated this task. Did it anyway. That's called being an adult.",
                f" High-hate task complete. You survived. The dread was worse than the doing. It always is.",
            ]
            response += random.choice(hate_additions)

        # Add priority/reminder context
        if priority >= 4 and completion_speed in ["slow", "glacial"]:
            # High priority but slow/glacial completion - mismatch
            priority_additions = [
                f" High priority task. Low priority execution. The math doesn't add up.",
                f" Critical deadline. Glacial pace. Someone explain that logic.",
                f" Urgent task. Non-urgent execution. Fascinating choices.",
            ]
            response += random.choice(priority_additions)
        elif priority >= 4 and completion_speed in ["blazing", "fast"]:
            # High priority and fast/blazing completion - rare competence
            priority_additions = [
                f" Critical task, fast execution. Competence. Novel.",
                f" High priority treated like high priority. Revolutionary.",
                f" Urgent task. Urgent execution. Who are you.",
            ]
            response += random.choice(priority_additions)

        # Add reminder count context
        if reminder_count >= 10:
            reminder_additions = [
                f" Took {reminder_count} reminders to get here. But we got here.",
                f" {reminder_count} harassment messages. Eventually, persistence wins.",
                f" After {reminder_count} reminders. Your resistance is well-documented.",
            ]
            response += random.choice(reminder_additions)
        elif reminder_count >= 5:
            reminder_additions = [
                f" {reminder_count} reminders. Not your finest performance.",
                f" Needed {reminder_count} nudges. Noted for next time.",
            ]
            response += random.choice(reminder_additions)

        return response

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user

        with get_db_context() as db:
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
            "💬 Chat & Motivation:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/rudeness [1-10] - Adjust rudeness intensity level\n\n"
            "📋 Task Management:\n"
            "/new - Create a new task (interactive)\n"
            "/list - View all your active tasks\n"
            "/done - Mark a task as completed\n"
            "/stats - View your statistics and task progress\n\n"
            "Just send me any message about what you're avoiding or procrastinating on, "
            "and I'll give you the motivation you need to get it done!\n\n"
            "Rudeness Levels:\n"
            "1-3: Sharp but not brutal\n"
            "4-6: Standard drill sergeant mode\n"
            "7-10: Maximum savage mode"
        )

        await update.message.reply_text(help_text)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show comprehensive user statistics including tasks"""
        user = update.effective_user

        try:
            with get_db_context() as db:
                db_ops = DatabaseOperations(db)
                user_obj = db_ops.get_or_create_user(telegram_id=user.id)
                conversations = db_ops.get_user_conversations(user_obj.id)
                task_stats = db_ops.get_task_stats(user_obj.id)

            # Format task statistics
            stats_lines = [
                "📊 Your RUDE.AI Stats:\n",
                f"Rudeness Level: {user_obj.rudeness_level}/10",
                f"Total interactions: {user_obj.interaction_count}",
                f"Excuse count: {user_obj.excuse_count}",
                f"Total conversations: {len(conversations)}",
                f"Member since: {user_obj.created_at.strftime('%Y-%m-%d')}\n",
                "─────────────────────",
                "📋 Task Statistics:\n",
                f"Active tasks: {task_stats['active']}",
                f"Completed tasks: {task_stats['completed']}",
                f"Expired tasks: {task_stats['expired']}",
            ]

            # Add average completion time if available
            if task_stats['avg_completion_hours'] is not None:
                avg_hours = task_stats['avg_completion_hours']
                if avg_hours < 1:
                    avg_minutes = int(avg_hours * 60)
                    stats_lines.append(f"Avg completion time: {avg_minutes} minutes")
                else:
                    stats_lines.append(f"Avg completion time: {avg_hours:.1f} hours")
            else:
                stats_lines.append("Avg completion time: N/A (no completed tasks)")

            message = "\n".join(stats_lines)

            # Add sarcastic commentary based on stats
            if task_stats['completed'] == 0 and task_stats['active'] > 0:
                message += "\n\n💬 You've created tasks but finished none. Classic."
            elif task_stats['completed'] > 0 and task_stats['active'] == 0:
                message += "\n\n💬 All caught up. This won't last."
            elif task_stats['active'] > task_stats['completed'] * 2:
                message += "\n\n💬 You're creating tasks faster than you complete them. Bold strategy."
            elif task_stats['avg_completion_hours'] and task_stats['avg_completion_hours'] > 24:
                message += "\n\n💬 Average completion time over a day. Efficiency incarnate."
            elif task_stats['completed'] >= 10:
                message += "\n\n💬 Double digits completed. I'm almost impressed."

            await update.message.reply_text(message)
            logger.info(f"User {user.id} viewed their stats")

        except Exception as e:
            logger.error(f"Error getting stats for user {user.id}: {e}")
            await update.message.reply_text(
                "Couldn't retrieve your stats. Even the database doesn't want to look."
            )

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin-only command to view system-wide statistics"""
        user = update.effective_user

        # Admin user ID check
        ADMIN_USER_ID = 1825306172

        if user.id != ADMIN_USER_ID:
            await update.message.reply_text(
                "This command is for the bot admin only. Nice try."
            )
            logger.warning(f"Unauthorized admin access attempt by user {user.id} (@{user.username})")
            return

        try:
            with get_db_context() as db:
                from sqlalchemy import text, func
                from rudeai_bot.models.user import User
                from rudeai_bot.models.task import Task

                # Total users
                total_users = db.query(func.count(User.id)).scalar()

                # Total tasks created
                total_tasks = db.query(func.count(Task.id)).scalar()

                # Tasks by status
                active_tasks = db.query(func.count(Task.id)).filter(Task.status == 'active').scalar()
                completed_tasks = db.query(func.count(Task.id)).filter(Task.status == 'completed').scalar()
                expired_tasks = db.query(func.count(Task.id)).filter(Task.status == 'expired').scalar()

                # Average task stats
                avg_hate = db.query(func.avg(Task.hate_level)).scalar()
                avg_priority = db.query(func.avg(Task.priority)).scalar()

                # Recent activity
                from datetime import datetime, timedelta, timezone
                last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
                recent_tasks = db.query(func.count(Task.id)).filter(Task.created_at >= last_24h).scalar()
                recent_completions = db.query(func.count(Task.id)).filter(
                    Task.status == 'completed',
                    Task.completed_at >= last_24h
                ).scalar()

            # Format admin stats message
            stats_lines = [
                "🔧 RUDE.AI ADMIN DASHBOARD\n",
                "═══════════════════════",
                "👥 USER STATS:",
                f"  Total users: {total_users}",
                "",
                "📋 TASK STATS:",
                f"  Total tasks created: {total_tasks}",
                f"  Active tasks: {active_tasks}",
                f"  Completed: {completed_tasks}",
                f"  Expired: {expired_tasks}",
                "",
                "📊 TASK AVERAGES:",
                f"  Avg hate level: {avg_hate:.1f}/5" if avg_hate else "  Avg hate level: N/A",
                f"  Avg priority: {avg_priority:.1f}/5" if avg_priority else "  Avg priority: N/A",
                "",
                "🕐 LAST 24 HOURS:",
                f"  Tasks created: {recent_tasks}",
                f"  Tasks completed: {recent_completions}",
                "",
                "═══════════════════════",
                f"Completion rate: {(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "Completion rate: N/A",
                f"Expiry rate: {(expired_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "Expiry rate: N/A"
            ]

            message = "\n".join(stats_lines)
            await update.message.reply_text(message)
            logger.info(f"Admin {user.id} viewed system stats")

        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            await update.message.reply_text(
                f"Error retrieving admin stats: {str(e)}"
            )

    async def scheduler_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin-only command to view scheduler status"""
        user = update.effective_user

        # Admin user ID check
        ADMIN_USER_ID = 1825306172

        if user.id != ADMIN_USER_ID:
            await update.message.reply_text(
                "This command is for the bot admin only. Nice try."
            )
            logger.warning(f"Unauthorized scheduler access attempt by user {user.id} (@{user.username})")
            return

        try:
            if not self.scheduler:
                await update.message.reply_text(
                    "❌ SCHEDULER NOT INITIALIZED\n\n"
                    "The scheduler was never created. This is a critical bug."
                )
                logger.error("Scheduler command called but self.scheduler is None!")
                return

            # Scheduler status
            is_running = self.scheduler.scheduler.running
            all_jobs = self.scheduler.scheduler.get_jobs()
            total_jobs = len(all_jobs)

            # Group jobs by task
            from collections import defaultdict
            task_jobs = defaultdict(list)
            expiry_jobs = []

            for job in all_jobs:
                if 'harassment' in job.id:
                    task_id = int(job.id.split('_')[1])
                    task_jobs[task_id].append(job)
                elif 'expiry' in job.id:
                    task_id = int(job.id.split('_')[1])
                    expiry_jobs.append((task_id, job))

            # Get test mode status
            from rudeai_bot.config.settings import settings
            test_mode = settings.scheduler_test_mode
            mode_str = "TEST MODE (240x faster)" if test_mode else "PRODUCTION MODE"

            # Format status message
            status_lines = [
                "⚙️ SCHEDULER STATUS\n",
                "═══════════════════════",
                f"Status: {'🟢 RUNNING' if is_running else '🔴 STOPPED'}",
                f"Mode: {mode_str}",
                f"Total jobs: {total_jobs}",
                "",
                f"📋 ACTIVE TASKS: {len(task_jobs)}",
            ]

            # Show details for each task with scheduled jobs
            if task_jobs:
                for task_id, jobs in sorted(task_jobs.items()):
                    harassment_count = len(jobs)
                    next_job = min(jobs, key=lambda j: j.next_run_time) if jobs else None

                    if next_job and next_job.next_run_time:
                        from datetime import datetime, timezone
                        now = datetime.now(timezone.utc)
                        time_until = next_job.next_run_time - now
                        minutes_until = int(time_until.total_seconds() / 60)

                        status_lines.append(
                            f"  Task {task_id}: {harassment_count} job(s), "
                            f"next in {minutes_until}min"
                        )
            else:
                status_lines.append("  (No active tasks)")

            status_lines.extend([
                "",
                f"⏱️  EXPIRY JOBS: {len(expiry_jobs)}",
            ])

            if expiry_jobs:
                for task_id, job in expiry_jobs:
                    if job.next_run_time:
                        from datetime import datetime, timezone
                        now = datetime.now(timezone.utc)
                        time_until = job.next_run_time - now
                        hours_until = time_until.total_seconds() / 3600
                        status_lines.append(f"  Task {task_id}: expires in {hours_until:.1f}h")

            status_lines.extend([
                "",
                "═══════════════════════",
                f"Reminder counts tracked: {len(self.scheduler.reminder_counts)}",
            ])

            # Show next upcoming job
            if all_jobs:
                next_job = min(all_jobs, key=lambda j: j.next_run_time if j.next_run_time else datetime.max.replace(tzinfo=timezone.utc))
                if next_job and next_job.next_run_time:
                    status_lines.append(f"\n⏰ Next job: {next_job.id}")
                    status_lines.append(f"   Runs at: {next_job.next_run_time}")

            message = "\n".join(status_lines)
            await update.message.reply_text(message)
            logger.info(f"Admin {user.id} viewed scheduler status")

        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}", exc_info=True)
            await update.message.reply_text(
                f"Error retrieving scheduler status: {str(e)}"
            )

    async def list_tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show all active tasks"""
        user = update.effective_user

        try:
            with get_db_context() as db:
                db_ops = DatabaseOperations(db)
                user_obj = db_ops.get_or_create_user(telegram_id=user.id)
                tasks = db_ops.get_active_tasks(user_obj.id)

            if not tasks:
                await update.message.reply_text(
                    "No tasks. Either you're productive or you've given up.\n\n"
                    "I'm guessing the latter."
                )
                return

            # Format task list
            task_lines = []
            for i, task in enumerate(tasks, 1):
                hate_emoji = "😤" * task.hate_level
                priority_emoji = "⚡" * task.priority
                time_ago = self._format_time_ago(task.created_at)

                task_lines.append(
                    f"{i}. {task.name}\n"
                    f"   {hate_emoji} Hate: {task.hate_level}/5  |  "
                    f"{priority_emoji} Priority: {task.priority}/5\n"
                    f"   Created {time_ago}"
                )

            task_count = len(tasks)
            header = f"You have {task_count} active task{'s' if task_count != 1 else ''}:\n\n"

            message = header + "\n\n".join(task_lines)
            message += "\n\nUse /done to mark a task complete."

            await update.message.reply_text(message)
            logger.info(f"User {user.id} listed {task_count} active tasks")

        except Exception as e:
            logger.error(f"Error listing tasks for user {user.id}: {e}")
            await update.message.reply_text(
                "Couldn't retrieve your tasks. The database is judging you."
            )

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

            with get_db_context() as db:
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
            with get_db_context() as db:
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
                with get_db_context() as db:
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

    # Task Management Handlers

    async def new_task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the task creation flow"""
        user = update.effective_user

        await update.message.reply_text(TaskCreationMessages.get_random_opening())

        logger.info(f"User {user.id} started task creation")
        return self.TASK_NAME

    async def task_name_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive task name and ask for hate level"""
        task_name = update.message.text.strip()

        if len(task_name) < 3:
            await update.message.reply_text(
                "That's not a task, that's an excuse. Try again with actual words."
            )
            return self.TASK_NAME

        # Store task name in context
        context.user_data['task_name'] = task_name

        await update.message.reply_text(
            f"'{task_name}'\n\n"
            "How much do you hate this task?\n"
            "1 = Mildly annoying\n"
            "2 = Pretty unpleasant\n"
            "3 = Really don't want to\n"
            "4 = Absolutely despise it\n"
            "5 = Would rather eat glass\n\n"
            "Pick a number 1-5:"
        )

        return self.TASK_HATE_LEVEL

    async def task_hate_level_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive hate level and ask for priority"""
        try:
            hate_level = int(update.message.text.strip())
            if not 1 <= hate_level <= 5:
                raise ValueError()
        except ValueError:
            await update.message.reply_text(
                "That's not a number between 1 and 5. Try again, genius."
            )
            return self.TASK_HATE_LEVEL

        # Store hate level
        context.user_data['task_hate_level'] = hate_level

        hate_responses = {
            1: "Barely a blip on the suffering scale.",
            2: "Unpleasant but survivable.",
            3: "Significant avoidance detected.",
            4: "Deep aversion noted.",
            5: "Maximum hatred achieved. Impressive."
        }

        await update.message.reply_text(
            f"{hate_responses[hate_level]}\n\n"
            "Now, how urgent is this?\n"
            "1 = Whenever, eventually\n"
            "2 = Should do soon-ish\n"
            "3 = Actually matters\n"
            "4 = Pretty damn urgent\n"
            "5 = Literally on fire\n\n"
            "Pick a number 1-5:"
        )

        return self.TASK_PRIORITY

    async def task_priority_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive priority and create the task"""
        user = update.effective_user

        try:
            priority = int(update.message.text.strip())
            if not 1 <= priority <= 5:
                raise ValueError()
        except ValueError:
            await update.message.reply_text(
                "1 through 5. How is this difficult?"
            )
            return self.TASK_PRIORITY

        # Get stored data
        task_name = context.user_data.get('task_name')
        hate_level = context.user_data.get('task_hate_level')

        # Create the task in database
        try:
            with get_db_context() as db:
                db_ops = DatabaseOperations(db)
                user_obj = db_ops.get_or_create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )

                task = db_ops.create_task(
                    user_id=user_obj.id,
                    name=task_name,
                    hate_level=hate_level,
                    priority=priority
                )

                # Extract primitive values BEFORE session closes to avoid detached instance errors
                task_id = task.id
                task_created_at = task.created_at
                user_db_id = user_obj.id

            # Schedule harassment and expiry jobs for the new task (using primitive values only)
            if self.scheduler:
                logger.info(f"📅 Scheduling jobs for new task {task_id} (priority={priority}, hate={hate_level})")
                self.scheduler.schedule_task_jobs(
                    task_id=task_id,
                    user_id=user_db_id,
                    telegram_id=user.id,  # From Telegram Update, not DB
                    task_name=task_name,
                    hate_level=hate_level,
                    priority=priority,
                    created_at=task_created_at
                )
            else:
                logger.warning(f"⚠️ Scheduler not set! Cannot schedule jobs for task {task_id}")

            # Send priority-based confirmation
            await update.message.reply_text(
                TaskCreationMessages.get_task_confirmation(task_name, priority, hate_level)
            )

            logger.info(f"Task created: {task_id} for user {user.id}")

            # Clear context data
            context.user_data.clear()

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error creating task for user {user.id}: {e}")
            await update.message.reply_text(
                "Something broke. Even I can't handle your incompetence right now."
            )
            context.user_data.clear()
            return ConversationHandler.END

    async def cancel_task_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the task creation flow"""
        await update.message.reply_text(
            "Giving up already? Typical.\n\n"
            "Come back when you grow a spine."
        )

        context.user_data.clear()
        return ConversationHandler.END

    async def done_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Mark a task as completed"""
        user = update.effective_user

        try:
            with get_db_context() as db:
                db_ops = DatabaseOperations(db)
                user_obj = db_ops.get_or_create_user(telegram_id=user.id)
                tasks = db_ops.get_active_tasks(user_obj.id)

            if not tasks:
                await update.message.reply_text(
                    "You have no active tasks to complete.\n\n"
                    "Either you're done for the day, or you never started."
                )
                return ConversationHandler.END

            if len(tasks) == 1:
                # Auto-complete the single task
                task = tasks[0]

                with get_db_context() as db:
                    db_ops = DatabaseOperations(db)
                    completed_task = db_ops.complete_task(task.id, user_obj.id)

                if completed_task:
                    # Get reminder count from scheduler before canceling jobs
                    reminder_count = 0
                    if self.scheduler:
                        reminder_count = self.scheduler.reminder_counts.get(completed_task.id, 0)
                        logger.info(f"Task {completed_task.id} received {reminder_count} harassment reminders")

                    # Cancel scheduled harassment and expiry jobs
                    logger.info(f"\n{'='*80}")
                    logger.info(f"✓ TASK COMPLETED: task_id={completed_task.id}, name='{completed_task.name}'")
                    logger.info(f"  Task details: hate_level={completed_task.hate_level}, priority={completed_task.priority}")
                    logger.info(f"  Now calling scheduler.cancel_task_jobs({completed_task.id})...")
                    logger.info(f"{'='*80}")
                    if self.scheduler:
                        self.scheduler.cancel_task_jobs(completed_task.id)
                    else:
                        logger.error(f"❌ CRITICAL: Scheduler is None! Cannot cancel jobs for task {completed_task.id}")

                    duration = completed_task.time_to_complete
                    response = self._get_completion_response(
                        completed_task.name,
                        duration,
                        completed_task.hate_level,
                        completed_task.priority,
                        reminder_count
                    )

                    await update.message.reply_text(
                        f"✓ {completed_task.name}\n\n{response}"
                    )
                    logger.info(f"User {user.id} completed task {task.id}")
                else:
                    await update.message.reply_text("Failed to mark task complete. Try again.")

                return ConversationHandler.END

            else:
                # Multiple tasks - ask which one
                task_lines = []
                for i, task in enumerate(tasks, 1):
                    time_ago = self._format_time_ago(task.created_at)
                    task_lines.append(
                        f"{i}. {task.name}\n"
                        f"   (Priority: {task.priority}/5, Created {time_ago})"
                    )

                # Store tasks in context
                context.user_data['completion_tasks'] = tasks

                message = "Which task did you actually finish?\n\n"
                message += "\n\n".join(task_lines)
                message += "\n\nType the number, or /cancel to back out."

                await update.message.reply_text(message)
                return self.TASK_SELECTION

        except Exception as e:
            logger.error(f"Error in done_command for user {user.id}: {e}")
            await update.message.reply_text("Something broke. Shocking.")
            return ConversationHandler.END

    async def task_selection_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle task selection for completion"""
        user = update.effective_user

        try:
            selection = int(update.message.text.strip())
            tasks = context.user_data.get('completion_tasks', [])

            if not 1 <= selection <= len(tasks):
                await update.message.reply_text(
                    f"Pick a number between 1 and {len(tasks)}. It's not complicated."
                )
                return self.TASK_SELECTION

            task = tasks[selection - 1]

            with get_db_context() as db:
                db_ops = DatabaseOperations(db)
                user_obj = db_ops.get_or_create_user(telegram_id=user.id)
                completed_task = db_ops.complete_task(task.id, user_obj.id)

            if completed_task:
                # Get reminder count from scheduler before canceling jobs
                reminder_count = 0
                if self.scheduler:
                    reminder_count = self.scheduler.reminder_counts.get(completed_task.id, 0)
                    logger.info(f"Task {completed_task.id} received {reminder_count} harassment reminders")

                # Cancel scheduled harassment and expiry jobs
                logger.info(f"\n{'='*80}")
                logger.info(f"✓ TASK COMPLETED: task_id={completed_task.id}, name='{completed_task.name}'")
                logger.info(f"  Task details: hate_level={completed_task.hate_level}, priority={completed_task.priority}")
                logger.info(f"  Now calling scheduler.cancel_task_jobs({completed_task.id})...")
                logger.info(f"{'='*80}")
                if self.scheduler:
                    self.scheduler.cancel_task_jobs(completed_task.id)
                else:
                    logger.error(f"❌ CRITICAL: Scheduler is None! Cannot cancel jobs for task {completed_task.id}")

                duration = completed_task.time_to_complete
                response = self._get_completion_response(
                    completed_task.name,
                    duration,
                    completed_task.hate_level,
                    completed_task.priority,
                    reminder_count
                )

                await update.message.reply_text(
                    f"✓ {completed_task.name}\n\n{response}"
                )
                logger.info(f"User {user.id} completed task {task.id}")
            else:
                await update.message.reply_text("Failed to mark task complete. Try again.")

            context.user_data.clear()
            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text(
                "That's not a number. Try again, or /cancel to give up."
            )
            return self.TASK_SELECTION
        except Exception as e:
            logger.error(f"Error completing task for user {user.id}: {e}")
            await update.message.reply_text("Something went wrong. As usual.")
            context.user_data.clear()
            return ConversationHandler.END

    async def cancel_task_completion(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel task completion flow"""
        await update.message.reply_text(
            "Fine. Leave it unfinished. What else is new."
        )
        context.user_data.clear()
        return ConversationHandler.END

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(f"Exception while handling an update: {context.error}")

        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "An error occurred. My circuits are too advanced for this nonsense."
                )
            except Exception:
                pass