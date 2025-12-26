"""Harassment message pools organized by hate level (tone)"""

import random
from rudeai_bot.config.settings import settings
from rudeai_bot.services.ai_service import AIHarassmentService
from loguru import logger


class HarassmentMessagePool:
    """
    Comprehensive message pools for task harassment.
    Messages are organized by HATE LEVEL (1-5), which controls TONE only.
    Frequency is controlled separately by priority.

    Uses AI-generated messages with fallback to static templates.
    """

    # Initialize AI service (class-level, shared across all instances)
    _ai_service = None

    @classmethod
    def _get_ai_service(cls):
        """Lazy initialization of AI service"""
        if cls._ai_service is None:
            cls._ai_service = AIHarassmentService()
        return cls._ai_service

    # Static message pools - used as fallback when AI is unavailable
    # Organized by hate level (tone)
    MESSAGES = {
        1: [  # Hate Level 1: Almost friendly nudge, minimal edge
            "{task_name}\n\nJust checking in. {time_context}.",
            "{task_name}\n\nStill on your list, I see. {time_context}.",
            "{task_name}\n\nReminder about this one. {time_context}.",
            "{task_name}\n\n{time_context}. Gentle nudge.",
            "{task_name}\n\nThought I'd mention this. {time_context}.",
            "{task_name}\n\n{time_context}. Still pending.",
        ],

        2: [  # Hate Level 2: Mild disappointment, light jabs
            "{task_name}\n\n{time_context}. Light procrastination detected.",
            "{task_name}\n\nMild disappointment setting in. {time_context}.",
            "{task_name}\n\n{time_context}. Starting to notice a pattern.",
            "{task_name}\n\nStill waiting. {time_context}. Interesting.",
            "{task_name}\n\n{time_context}. The avoidance continues.",
            "{task_name}\n\n{time_context}. You're testing my patience. Mildly.",
        ],

        3: [  # Hate Level 3: Dry, sarcastic, classic House
            "{task_name}\n\n{time_context}. Classic avoidance behavior.",
            "{task_name}\n\nStill waiting. {time_context}. Shocking.",
            "{task_name}\n\n{time_context}. Your commitment to delay is impressive.",
            "{task_name}\n\nHow long are we doing this? {time_context}.",
            "{task_name}\n\n{time_context}. Procrastination as performance art.",
            "{task_name}\n\n{time_context}. I'd be impressed if I cared.",
        ],

        4: [  # Hate Level 4: Sharp and pointed, no patience
            "{task_name}\n\n{time_context}. Your excuses are noted and dismissed.",
            "{task_name}\n\nSeriously? {time_context}. Move.",
            "{task_name}\n\n{time_context}. This is pathetic.",
            "{task_name}\n\nEnough. {time_context}. Do it now.",
            "{task_name}\n\n{time_context}. Zero tolerance for this nonsense.",
            "{task_name}\n\n{time_context}. Stop wasting my time and yours.",
        ],

        5: [  # Hate Level 5: Savage, theatrical, House at his worst
            "{task_name}\n\n{time_context}. You hate it and it's still not done. Pathetic.",
            "{task_name}\n\n{time_context}. Maximum hatred, zero action. Classic you.",
            "{task_name}\n\n{time_context}. I'm documenting your incompetence for posterity.",
            "{task_name}\n\n{time_context}. The universe is judging you. So am I.",
            "{task_name}\n\n{time_context}. Your capacity for avoidance is truly breathtaking.",
            "{task_name}\n\n{time_context}. Maximum priority. Maximum hatred. Minimum execution.",
        ]
    }

    # Special 12-hour check-in messages
    CHECKIN_12HR_MESSAGES = [
        "{task_name}\n\n12-hour check-in. Still not done? Remarkable.",
        "{task_name}\n\nHalfway to expiry. Zero progress. On brand.",
        "{task_name}\n\n12 hours in. Task status: still avoided.",
        "{task_name}\n\nMidpoint reached. Achievement: procrastination.",
        "{task_name}\n\n12-hour mark. The task remains. Your excuses don't matter.",
    ]

    @staticmethod
    def _get_time_context(hours_old: float) -> str:
        """Generate time context string based on task age"""
        test_mode = settings.scheduler_test_mode

        if test_mode:
            # Show actual elapsed time in test mode for debugging
            if hours_old < 0.01:  # Less than ~36 seconds
                return f"{int(hours_old * 3600)} seconds in"
            elif hours_old < 0.1:  # Less than 6 minutes
                return f"{int(hours_old * 60)} minutes in"
            else:
                return f"{hours_old:.1f} hours in"
        else:
            # Production mode - contextual phrases
            if hours_old < 1:
                return "Less than an hour in"
            elif hours_old < 4:
                return f"{int(hours_old)} hours in"
            elif hours_old < 12:
                return f"{int(hours_old)} hours in. Half a day wasted"
            elif hours_old < 20:
                return f"{int(hours_old)} hours in. Almost a full day of avoidance"
            else:
                return f"{int(hours_old)} hours in. Impressive dedication to doing nothing"

    @classmethod
    def get_message(cls, task_name: str, hate_level: int, hours_old: float,
                   is_12hr_checkin: bool = False, reminder_count: int = 1) -> str:
        """
        Get harassment message based on hate level (tone).

        Uses AI generation first, falls back to static templates if unavailable.

        Args:
            task_name: Name of the task
            hate_level: 1-5, controls tone/severity (NOT frequency)
            hours_old: How long task has existed (for time context)
            is_12hr_checkin: True if this is the special 12-hour check-in
            reminder_count: Which reminder this is (for AI escalation)

        Returns:
            Formatted harassment message
        """

        # Clamp hate_level to valid range
        hate_level = max(1, min(5, hate_level))

        # Get time context for AI and fallback
        time_context = cls._get_time_context(hours_old)

        # Try AI generation first
        ai_service = cls._get_ai_service()
        if ai_service.enabled:
            ai_message = ai_service.generate_harassment_message(
                task_name=task_name,
                time_elapsed=time_context,
                hate_level=hate_level,
                reminder_count=reminder_count,
                is_12hr_checkin=is_12hr_checkin
            )

            if ai_message:
                logger.debug(f"✨ Using AI-generated message (hate={hate_level}, reminder={reminder_count})")
                return ai_message
            else:
                logger.debug(f"⚠️ AI generation failed, using static fallback")

        # Fallback to static messages
        logger.debug(f"📝 Using static message (hate={hate_level})")

        # Special 12-hour check-in message
        if is_12hr_checkin:
            template = random.choice(cls.CHECKIN_12HR_MESSAGES)
            return template.format(task_name=task_name)

        # Select random message from hate level pool
        template = random.choice(cls.MESSAGES[hate_level])

        # Format with task details
        return template.format(
            task_name=task_name,
            time_context=time_context
        )
