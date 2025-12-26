from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from rudeai_bot.database.base import Base


class TaskStatus(enum.Enum):
    """Task status enum"""
    active = "active"
    completed = "completed"
    expired = "expired"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    hate_level = Column(Integer, nullable=False)  # 1-5: how much user hates this task
    priority = Column(Integer, nullable=False)  # 1-5: task priority
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.active, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    user = relationship("User", backref="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, name='{self.name[:30]}', status={self.status.value})>"

    @property
    def time_to_complete(self):
        """Calculate time taken to complete (in seconds)"""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None

    @property
    def expiry_hours(self) -> float:
        """Get task expiry time in hours"""
        from rudeai_bot.config.settings import settings
        from rudeai_bot.services.scheduler_service import TEST_MODE_SCALE_FACTOR

        test_mode = settings.scheduler_test_mode

        if test_mode:
            return 24 / TEST_MODE_SCALE_FACTOR  # ~6 minutes (24hrs / 240)
        else:
            return 24.0  # 24 hours

    @property
    def is_expired(self) -> bool:
        """Check if task has been active for more than expiry time"""
        from datetime import datetime, timezone, timedelta

        if self.status != TaskStatus.active:
            return False

        if self.created_at.tzinfo is None:
            created_at = self.created_at.replace(tzinfo=timezone.utc)
        else:
            created_at = self.created_at

        age = datetime.now(timezone.utc) - created_at
        return age > timedelta(hours=self.expiry_hours)
