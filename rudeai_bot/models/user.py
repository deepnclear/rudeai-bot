from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from rudeai_bot.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    rudeness_level = Column(Integer, default=5)
    interaction_count = Column(Integer, default=0)
    excuse_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"