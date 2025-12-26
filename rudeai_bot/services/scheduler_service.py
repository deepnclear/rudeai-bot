import os
import random
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from loguru import logger
from telegram import Bot

from rudeai_bot.config.settings import settings
from rudeai_bot.services.harassment_messages import HarassmentMessagePool


# Test mode scaling constant
TEST_MODE_SCALE_FACTOR = 240  # All intervals are 240x faster in test mode


def get_local_time(dt_utc: datetime) -> datetime:
    """Convert UTC datetime to system local time"""
    # Ensure datetime is timezone-aware
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone()


def adjust_for_quiet_hours(dt: datetime, test_mode: bool = False, quiet_hour_offset_minutes: int = 0) -> datetime:
    """
    Adjust datetime if it falls in quiet hours (11pm - 7am).
    If in quiet period, shift to 7am same day (or next day if already past 7am).

    In test mode, time flows 240x faster but quiet hours are same wall-clock times.

    Args:
        dt: Datetime to check (should be timezone-aware)
        test_mode: Whether in test mode
        quiet_hour_offset_minutes: Additional offset to add to 7am (for spacing multiple messages)

    Returns:
        Adjusted datetime (may be same as input if not in quiet hours)
    """
    local_dt = get_local_time(dt)
    hour = local_dt.hour

    # Check if in quiet hours (11pm to 7am)
    if hour >= 23 or hour < 7:
        # Calculate next 7am
        if hour >= 23:
            # After 11pm, move to 7am next day
            next_7am = local_dt.replace(hour=7, minute=0, second=0, microsecond=0) + timedelta(days=1)
        else:
            # Before 7am, move to 7am same day
            next_7am = local_dt.replace(hour=7, minute=0, second=0, microsecond=0)

        # Add offset for spacing multiple messages at 7am
        next_7am = next_7am + timedelta(minutes=quiet_hour_offset_minutes)

        # Convert back to UTC
        return next_7am.astimezone(timezone.utc)

    return dt


def get_priority_intervals(priority: int) -> dict:
    """
    Get early and late intervals for a priority level.

    Args:
        priority: Priority level (1-5)

    Returns:
        Dictionary with 'early' and 'late' interval minutes
    """
    intervals_map = {
        5: {'early': 60, 'late': 90},      # 1hr → 1.5hrs
        4: {'early': 90, 'late': 120},     # 1.5hrs → 2hrs
        3: {'early': 120, 'late': 180},    # 2hrs → 3hrs
        2: {'early': 180, 'late': 240},    # 3hrs → 4hrs
        1: {'early': 240, 'late': 240},    # 4hrs → 4hrs (no change)
    }

    return intervals_map.get(priority, intervals_map[3])  # Default to priority 3


def calculate_message_schedule(created_at: datetime, priority: int, test_mode: bool = False) -> list:
    """
    Calculate all harassment message times based on priority.

    Args:
        created_at: When the task was created (timezone-aware)
        priority: Priority level (1-5)
        test_mode: Whether in test mode

    Returns:
        List of dicts with:
        - 'scheduled_time': datetime when message should fire
        - 'is_12hr_checkin': bool, True for the 12hr check-in message
        - 'interval_type': str describing the interval ('first', 'early', 'late', '12hr', 'final')
    """
    schedule = []
    scale = TEST_MODE_SCALE_FACTOR if test_mode else 1

    # Ensure created_at is timezone-aware
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    # Track quiet hour adjustments for proper spacing
    # Maps each 7am boundary (date) to count of messages shifted there
    quiet_hour_7am_counts = {}

    def apply_quiet_hours_with_spacing(dt):
        """Apply quiet hours adjustment with 10-minute spacing for collisions at 7am"""
        # Check if this time falls in quiet hours
        local_dt = get_local_time(dt)
        hour = local_dt.hour

        if hour >= 23 or hour < 7:
            # Will be shifted to 7am - calculate which 7am
            if hour >= 23:
                target_7am = local_dt.replace(hour=7, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else:
                target_7am = local_dt.replace(hour=7, minute=0, second=0, microsecond=0)

            # Track how many messages have been shifted to this specific 7am
            target_date = target_7am.date()
            if target_date not in quiet_hour_7am_counts:
                quiet_hour_7am_counts[target_date] = 0

            # Apply 10-minute spacing: 7:00, 7:10, 7:20, etc.
            offset_minutes = quiet_hour_7am_counts[target_date] * 10
            quiet_hour_7am_counts[target_date] += 1

            return adjust_for_quiet_hours(dt, test_mode, offset_minutes)
        else:
            # Not in quiet hours, no adjustment needed
            return adjust_for_quiet_hours(dt, test_mode, 0)

    # First message: 20 minutes after creation
    first_msg_time = created_at + timedelta(minutes=20/scale)
    first_msg_time = apply_quiet_hours_with_spacing(first_msg_time)
    schedule.append({
        'scheduled_time': first_msg_time,
        'is_12hr_checkin': False,
        'interval_type': 'first'
    })

    # Priority-based intervals
    intervals = get_priority_intervals(priority)
    early_interval = intervals['early']  # minutes
    late_interval = intervals['late']    # minutes
    cutoff_hours = 4  # Switch from early to late after 4 hours

    current_time = created_at + timedelta(minutes=20/scale)  # Start after first message
    cutoff_time = created_at + timedelta(hours=cutoff_hours/scale)
    expiry_time = created_at + timedelta(hours=24/scale)

    # Schedule messages until expiry (24 hours)
    while current_time < expiry_time:
        # Determine interval based on whether we're before or after 4hr cutoff
        if current_time < cutoff_time:
            interval_minutes = early_interval
            interval_type = 'early'
        else:
            interval_minutes = late_interval
            interval_type = 'late'

        current_time += timedelta(minutes=interval_minutes/scale)

        # Don't schedule beyond expiry
        if current_time >= expiry_time:
            # Priority 1 gets one final message before expiry
            if priority == 1:
                final_time = expiry_time - timedelta(minutes=30/scale)
                final_time = apply_quiet_hours_with_spacing(final_time)
                schedule.append({
                    'scheduled_time': final_time,
                    'is_12hr_checkin': False,
                    'interval_type': 'final'
                })
            break

        msg_time = apply_quiet_hours_with_spacing(current_time)
        schedule.append({
            'scheduled_time': msg_time,
            'is_12hr_checkin': False,
            'interval_type': interval_type
        })

    # Add 12hr check-in for priority 1-2 only
    if priority in [1, 2]:
        checkin_time = created_at + timedelta(hours=12/scale)
        if checkin_time < expiry_time:
            checkin_time = apply_quiet_hours_with_spacing(checkin_time)
            schedule.append({
                'scheduled_time': checkin_time,
                'is_12hr_checkin': True,
                'interval_type': '12hr'
            })

    # Log quiet hours adjustments
    total_quiet_hour_shifts = sum(quiet_hour_7am_counts.values())
    if total_quiet_hour_shifts > 0:
        logger.debug(f"🌙 Quiet hours: Shifted {total_quiet_hour_shifts} message(s) to 7am with 10min spacing")
        for date, count in quiet_hour_7am_counts.items():
            if count > 1:
                logger.debug(f"   • {date}: {count} messages (7:00, 7:10, 7:20, ...)")

    # Sort by scheduled time
    schedule.sort(key=lambda x: x['scheduled_time'])

    # COLLISION DETECTION AND PREVENTION
    # Check for messages within 15 minutes of each other and space them out
    logger.debug(f"🔍 Checking for message collisions (15min threshold)...")

    i = 0
    collision_count = 0
    while i < len(schedule) - 1:
        current_time = schedule[i]['scheduled_time']
        next_time = schedule[i + 1]['scheduled_time']

        time_diff_seconds = (next_time - current_time).total_seconds()
        time_diff_minutes = time_diff_seconds / 60

        if time_diff_minutes < 15:
            # Collision detected! Shift the later message
            shift_amount = 15 - time_diff_minutes  # Minutes to add
            schedule[i + 1]['scheduled_time'] = next_time + timedelta(minutes=shift_amount)

            collision_count += 1
            logger.debug(
                f"  ⚠️  Collision #{collision_count}: Messages {i} and {i+1} were {time_diff_minutes:.1f}min apart"
            )
            logger.debug(
                f"     Shifted message {i+1} by +{shift_amount:.1f}min to prevent collision"
            )

            # Re-sort after shifting (in case we created a new collision downstream)
            schedule.sort(key=lambda x: x['scheduled_time'])

            # Don't increment i - check this position again after re-sorting
            continue

        i += 1

    if collision_count > 0:
        logger.info(f"✅ Resolved {collision_count} message collision(s) - all messages now 15+ min apart")
    else:
        logger.debug(f"✅ No collisions detected - all messages naturally 15+ min apart")

    return schedule


class TaskSchedulerService:
    """Service for scheduling task harassment and expiry jobs"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()

        # Track reminder counts for AI escalation
        # Maps task_id -> reminder_count
        self.reminder_counts = {}

        test_mode = settings.scheduler_test_mode
        mode_str = "TEST MODE (240x faster)" if test_mode else "PRODUCTION MODE"
        logger.info(f"TaskSchedulerService initialized - {mode_str}")

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            test_mode = settings.scheduler_test_mode
            mode_str = "TEST MODE (15s intervals)" if test_mode else "PRODUCTION MODE (30min+ intervals)"
            logger.info(f"✅ Task scheduler started - {mode_str}")
            logger.info(f"✅ Scheduler state: running={self.scheduler.running}")
        else:
            logger.warning("⚠️ Scheduler already running")

    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("❌ Task scheduler stopped")

    def _get_job_id(self, task_id: int, job_type: str) -> str:
        """Generate unique job ID for a task"""
        return f"task_{task_id}_{job_type}"

    async def _send_harassment_message(self, telegram_id: int, task_id: int, task_name: str,
                                       hate_level: int, created_at, is_12hr_checkin: bool = False):
        """Send a harassment message to user about their task"""

        # Increment and track reminder count for this task
        if task_id not in self.reminder_counts:
            self.reminder_counts[task_id] = 0
        self.reminder_counts[task_id] += 1
        reminder_count = self.reminder_counts[task_id]

        logger.info(f"🔔 Harassment job triggered for task {task_id} (hate={hate_level}, 12hr={is_12hr_checkin}, reminder #{reminder_count})")

        try:
            # Calculate how old the task is
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            age = datetime.now(timezone.utc) - created_at
            hours_old = age.total_seconds() / 3600

            # Get message from pool (AI-powered with fallback)
            message = HarassmentMessagePool.get_message(
                task_name=task_name,
                hate_level=hate_level,
                hours_old=hours_old,
                is_12hr_checkin=is_12hr_checkin,
                reminder_count=reminder_count
            )

            logger.info(f"📤 Sending harassment #{reminder_count} (hate={hate_level}) to telegram_id={telegram_id}")
            await self.bot.send_message(chat_id=telegram_id, text=message)
            logger.info(f"✅ Sent harassment message for task {task_id} (hate={hate_level}, reminder #{reminder_count})")

        except Exception as e:
            logger.error(f"❌ Failed to send harassment message for task {task_id}: {e}", exc_info=True)

    async def _expire_task(self, task_id: int, user_id: int, telegram_id: int, task_name: str):
        """Expire a task and notify user"""
        try:
            from rudeai_bot.database.base import get_db_context
            from rudeai_bot.database.operations import DatabaseOperations
            from rudeai_bot.models.task import TaskStatus

            # Mark task as expired in database
            with get_db_context() as db:
                db_ops = DatabaseOperations(db)
                task = db_ops.get_task_by_id(task_id, user_id)

                if task and task.status == TaskStatus.active:
                    task.status = TaskStatus.expired
                    db.commit()
                    logger.info(f"⏱ Task {task_id} marked as expired")

            # Cancel all harassment jobs (there may be multiple)
            # Expiry job will auto-remove after execution
            idx = 0
            while True:
                job_id = f"task_{task_id}_harassment_{idx}"
                if self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
                    idx += 1
                else:
                    break

            if idx > 0:
                logger.info(f"🚫 Cancelled {idx} harassment job(s) for expired task {task_id}")

            # Send neutral expiry message
            test_mode = settings.scheduler_test_mode
            time_str = "2 minutes" if test_mode else "24 hours"

            message = f"⏱ Task expired: {task_name}\n\nYou didn't do it after {time_str}. Noted."
            await self.bot.send_message(chat_id=telegram_id, text=message)
            logger.info(f"📭 Sent expiry notification for task {task_id}")

        except Exception as e:
            logger.error(f"❌ Failed to expire task {task_id}: {e}")

    def schedule_task_jobs(self, task_id: int, user_id: int, telegram_id: int, task_name: str,
                          hate_level: int, priority: int, created_at):
        """Schedule harassment and expiry jobs for a task"""
        try:
            test_mode = settings.scheduler_test_mode

            logger.info(f"\n{'='*80}")
            logger.info(f"📅 SCHEDULING JOBS FOR task_id={task_id}")
            logger.info(f"  Task name: '{task_name}'")
            logger.info(f"  Priority: {priority}, Hate level: {hate_level}")
            logger.info(f"  Created at: {created_at}")
            logger.info(f"{'='*80}")

            # Calculate message schedule based on priority
            message_schedule = calculate_message_schedule(created_at, priority, test_mode)

            logger.info(f"📋 Will create {len(message_schedule)} harassment job(s):")
            created_job_ids = []

            # Schedule individual DateTrigger jobs for each message
            for idx, msg_info in enumerate(message_schedule):
                job_id = f"task_{task_id}_harassment_{idx}"

                self.scheduler.add_job(
                    self._send_harassment_message,
                    trigger=DateTrigger(run_date=msg_info['scheduled_time']),
                    args=[
                        telegram_id,
                        task_id,
                        task_name,
                        hate_level,
                        created_at,
                        msg_info['is_12hr_checkin']
                    ],
                    id=job_id,
                    replace_existing=True,
                    max_instances=1
                )

                created_job_ids.append(job_id)
                logger.info(
                    f"  ✓ Created: {job_id} - "
                    f"{msg_info['interval_type']} at {msg_info['scheduled_time']} "
                    f"(12hr={msg_info['is_12hr_checkin']})"
                )

            # Schedule expiry job
            scale = TEST_MODE_SCALE_FACTOR if test_mode else 1
            expiry_hours = 24 / scale

            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            expiry_time = created_at + timedelta(hours=expiry_hours)
            expiry_job_id = self._get_job_id(task_id, "expiry")

            self.scheduler.add_job(
                self._expire_task,
                trigger=DateTrigger(run_date=expiry_time),
                args=[task_id, user_id, telegram_id, task_name],
                id=expiry_job_id,
                replace_existing=True
            )

            created_job_ids.append(expiry_job_id)
            logger.info(f"  ✓ Created: {expiry_job_id} - expiry at {expiry_time}")

            mode_indicator = "🧪 TEST" if test_mode else "🚀 PROD"

            # Log scheduled job details
            logger.info(f"\n📊 SUMMARY:")
            logger.info(
                f"  {mode_indicator} Created {len(created_job_ids)} total jobs for task_id={task_id}"
            )
            logger.info(f"  Job IDs created: {', '.join(created_job_ids)}")
            logger.info(f"  Total scheduler jobs now: {len(self.scheduler.get_jobs())}")

            # Initialize reminder count for this task
            self.reminder_counts[task_id] = 0
            logger.debug(f"  📝 Initialized reminder count for task {task_id}")

            logger.info(f"{'='*80}\n")

        except Exception as e:
            logger.error(f"❌ Failed to schedule jobs for task {task_id}: {e}", exc_info=True)

    def cancel_task_jobs(self, task_id: int):
        """Cancel all scheduled jobs for a task"""
        try:
            if not self.scheduler.running:
                logger.warning(f"⚠️ Scheduler not running! Cannot cancel jobs for task {task_id}")
                return

            logger.info(f"\n{'='*80}")
            logger.info(f"🔍 DEBUG: Attempting to cancel jobs for task_id={task_id}")
            logger.info(f"{'='*80}")

            # List ALL jobs in scheduler BEFORE cancellation
            all_jobs_before = self.scheduler.get_jobs()
            logger.info(f"📋 ALL JOBS IN SCHEDULER BEFORE CANCELLATION ({len(all_jobs_before)} total):")
            for job in all_jobs_before:
                logger.info(f"  - Job ID: {job.id}, Next run: {job.next_run_time}")

            # Build list of job IDs we're going to try to cancel
            logger.info(f"\n🎯 JOB IDs WE'RE TRYING TO CANCEL:")
            job_ids_to_cancel = []

            # Check for harassment jobs
            idx = 0
            while idx < 100:  # Safety limit
                job_id = f"task_{task_id}_harassment_{idx}"
                job_ids_to_cancel.append(job_id)
                logger.info(f"  - Will try: {job_id}")
                if self.scheduler.get_job(job_id) is None:
                    break
                idx += 1

            # Check for expiry job
            expiry_job_id = self._get_job_id(task_id, "expiry")
            job_ids_to_cancel.append(expiry_job_id)
            logger.info(f"  - Will try: {expiry_job_id}")

            cancelled_jobs = []

            # NEW APPROACH: Find ALL jobs that belong to this task
            # Instead of guessing the pattern, scan all jobs and match by task_id
            logger.info(f"\n🔍 SEARCHING ALL JOBS FOR task_id={task_id}:")

            task_prefix = f"task_{task_id}_"
            jobs_to_cancel = []

            for job in all_jobs_before:
                if job.id.startswith(task_prefix):
                    jobs_to_cancel.append(job)
                    logger.info(f"  ✓ MATCHED: {job.id} (next run: {job.next_run_time})")

            if not jobs_to_cancel:
                logger.warning(f"  ✗ NO JOBS FOUND with prefix '{task_prefix}'")

            logger.info(f"\n🗑️ REMOVING {len(jobs_to_cancel)} MATCHED JOB(S):")

            # Cancel all matched jobs
            for job in jobs_to_cancel:
                try:
                    logger.info(f"  → Removing {job.id}...")
                    self.scheduler.remove_job(job.id)
                    cancelled_jobs.append(job.id)
                    logger.info(f"    ✓ Removed successfully")
                except Exception as e:
                    logger.error(f"    ✗ Failed to remove {job.id}: {e}")

            # List ALL jobs in scheduler AFTER cancellation
            logger.info(f"\n📋 ALL JOBS IN SCHEDULER AFTER CANCELLATION:")
            all_jobs_after = self.scheduler.get_jobs()
            if all_jobs_after:
                for job in all_jobs_after:
                    logger.info(f"  - Job ID: {job.id}, Next run: {job.next_run_time}")
            else:
                logger.info(f"  (No jobs remaining)")

            logger.info(f"\n📊 SUMMARY:")
            logger.info(f"  - Jobs before: {len(all_jobs_before)}")
            logger.info(f"  - Jobs cancelled: {len(cancelled_jobs)}")
            logger.info(f"  - Jobs after: {len(all_jobs_after)}")
            logger.info(f"  - Expected after: {len(all_jobs_before) - len(cancelled_jobs)}")

            if cancelled_jobs:
                logger.info(f"\n🚫 Cancelled these jobs: {', '.join(cancelled_jobs)}")

                # Verify jobs are actually gone
                verification_failed = []
                for job_id in cancelled_jobs:
                    if self.scheduler.get_job(job_id):
                        verification_failed.append(job_id)

                if verification_failed:
                    logger.error(
                        f"\n❌ VERIFICATION FAILED! These jobs still exist after cancellation: "
                        f"{', '.join(verification_failed)}"
                    )
                else:
                    logger.info(f"✅ Verified: All {len(cancelled_jobs)} job(s) successfully removed")
            else:
                logger.warning(
                    f"\n⚠️ WARNING: No jobs found to cancel for task {task_id}!"
                )
                logger.warning(f"   This could mean:")
                logger.warning(f"   1. Jobs were never scheduled for this task")
                logger.warning(f"   2. Jobs already fired and removed themselves")
                logger.warning(f"   3. Task ID mismatch between creation and completion")

            logger.info(f"{'='*80}\n")

            # Clean up reminder count tracking
            if task_id in self.reminder_counts:
                del self.reminder_counts[task_id]
                logger.debug(f"🗑️  Cleared reminder count for task {task_id}")

        except Exception as e:
            logger.error(f"❌ Failed to cancel jobs for task {task_id}: {e}", exc_info=True)

    async def reschedule_all_active_tasks(self):
        """Reschedule jobs for all active tasks (called on startup)"""
        try:
            from rudeai_bot.database.base import get_db_context
            from rudeai_bot.models.task import Task, TaskStatus
            from sqlalchemy.orm import joinedload

            with get_db_context() as db:
                # Get all active tasks with user relationship eagerly loaded
                tasks = db.query(Task).options(
                    joinedload(Task.user)
                ).filter(Task.status == TaskStatus.active).all()

                if not tasks:
                    logger.info("No active tasks to reschedule")
                    return

                logger.info(f"♻️ Rescheduling {len(tasks)} active task(s) on startup")

                for task in tasks:
                    # Extract primitive values to avoid detached instance errors
                    task_id = task.id
                    user_id = task.user_id
                    telegram_id = task.user.telegram_id
                    task_name = task.name
                    hate_level = task.hate_level
                    priority = task.priority
                    created_at = task.created_at
                    is_expired = task.is_expired

                    # Check if already expired
                    if is_expired:
                        logger.info(f"Task {task_id} is already expired, expiring now")
                        await self._expire_task(
                            task_id,
                            user_id,
                            telegram_id,
                            task_name
                        )
                    else:
                        # Schedule jobs for active task
                        self.schedule_task_jobs(
                            task_id=task_id,
                            user_id=user_id,
                            telegram_id=telegram_id,
                            task_name=task_name,
                            hate_level=hate_level,
                            priority=priority,
                            created_at=created_at
                        )

                logger.info("✅ All active tasks rescheduled successfully")

        except Exception as e:
            logger.error(f"❌ Failed to reschedule active tasks: {e}")
