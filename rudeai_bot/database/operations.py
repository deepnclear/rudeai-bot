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