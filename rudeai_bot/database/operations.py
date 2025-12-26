from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from loguru import logger

from rudeai_bot.models.user import User
from rudeai_bot.models.conversation import Conversation


class DatabaseOperations:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, telegram_id: int, username: Optional[str] = None,
                          first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        user = self.db.query(User).filter(User.telegram_id == telegram_id).first()

        if user:
            if user.username != username or user.first_name != first_name or user.last_name != last_name:
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                self.db.commit()
                self.db.refresh(user)
            return user

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )

        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Created new user: {user.telegram_id}")
            return user
        except IntegrityError:
            self.db.rollback()
            return self.db.query(User).filter(User.telegram_id == telegram_id).first()

    def save_conversation(self, user_id: int, user_message: str, bot_response: str) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            user_message=user_message,
            bot_response=bot_response
        )

        try:
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            logger.info(f"Saved conversation for user {user_id}")
            return conversation
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving conversation: {e}")
            raise

    def get_user_conversations(self, user_id: int, limit: int = 10) -> list[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .all()
        )

    def update_user_rudeness_level(self, user_id: int, rudeness_level: int) -> None:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.rudeness_level = max(1, min(10, rudeness_level))
            self.db.commit()
            self.db.refresh(user)

    def increment_user_interaction(self, user_id: int) -> None:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.interaction_count += 1
            self.db.commit()

    def increment_user_excuses(self, user_id: int) -> None:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.excuse_count += 1
            self.db.commit()

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()

    # Task Management Operations

    def create_task(self, user_id: int, name: str, hate_level: int, priority: int):
        """Create a new task"""
        from rudeai_bot.models.task import Task, TaskStatus

        task = Task(
            user_id=user_id,
            name=name,
            hate_level=max(1, min(5, hate_level)),  # Clamp to 1-5
            priority=max(1, min(5, priority)),  # Clamp to 1-5
            status=TaskStatus.active
        )

        try:
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            logger.info(f"Created task {task.id} for user {user_id}")
            return task
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating task: {e}")
            raise

    def get_active_tasks(self, user_id: int) -> list:
        """Get all active tasks for a user, ordered by priority (high to low) then hate_level"""
        from rudeai_bot.models.task import Task, TaskStatus

        return (
            self.db.query(Task)
            .filter(Task.user_id == user_id, Task.status == TaskStatus.active)
            .order_by(Task.priority.desc(), Task.hate_level.desc())
            .all()
        )

    def get_task_by_id(self, task_id: int, user_id: int) -> Optional:
        """Get a specific task by ID for a user"""
        from rudeai_bot.models.task import Task

        return (
            self.db.query(Task)
            .filter(Task.id == task_id, Task.user_id == user_id)
            .first()
        )

    def complete_task(self, task_id: int, user_id: int) -> Optional:
        """Mark a task as completed"""
        from rudeai_bot.models.task import Task, TaskStatus
        from datetime import datetime, timezone

        task = self.get_task_by_id(task_id, user_id)
        if task and task.status == TaskStatus.active:
            task.status = TaskStatus.completed
            task.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(task)
            logger.info(f"Completed task {task_id} for user {user_id}")
            return task
        return None

    def get_task_stats(self, user_id: int) -> dict:
        """Get task statistics for a user"""
        from rudeai_bot.models.task import Task, TaskStatus
        from sqlalchemy import func as sql_func

        # Count by status
        completed_count = (
            self.db.query(sql_func.count(Task.id))
            .filter(Task.user_id == user_id, Task.status == TaskStatus.completed)
            .scalar() or 0
        )

        expired_count = (
            self.db.query(sql_func.count(Task.id))
            .filter(Task.user_id == user_id, Task.status == TaskStatus.expired)
            .scalar() or 0
        )

        active_count = (
            self.db.query(sql_func.count(Task.id))
            .filter(Task.user_id == user_id, Task.status == TaskStatus.active)
            .scalar() or 0
        )

        # Average completion time (in hours)
        completed_tasks = (
            self.db.query(Task)
            .filter(Task.user_id == user_id, Task.status == TaskStatus.completed)
            .all()
        )

        avg_completion_time = None
        if completed_tasks:
            times = [t.time_to_complete for t in completed_tasks if t.time_to_complete]
            if times:
                avg_completion_time = sum(times) / len(times) / 3600  # Convert to hours

        return {
            "active": active_count,
            "completed": completed_count,
            "expired": expired_count,
            "avg_completion_hours": avg_completion_time
        }