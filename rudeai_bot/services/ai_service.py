import asyncio
import os
import re
from typing import Optional, List
from openai import AsyncOpenAI, OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger

from rudeai_bot.config.settings import settings


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.excuse_patterns = [
            r'\btoo tired\b', r'\btoo busy\b', r'\bno time\b', r'\blater\b',
            r'\btomorrow\b', r'\bnot today\b', r'\bmaybe\b', r'\bprocrastinat\w+\b',
            r'\bavoid\w+\b', r'\bdelay\w+\b', r'\bpostpon\w+\b', r'\bcan\'?t\b'
        ]

    def _detect_excuses(self, message: str) -> bool:
        message_lower = message.lower()
        return any(re.search(pattern, message_lower) for pattern in self.excuse_patterns)

    def _build_system_prompt(self, rudeness_level: int, excuse_count: int, recent_conversations: List[str]) -> str:
        base_personality = (
            "You are RUDE.AI, a brutal productivity drill sergeant.\n\n"
            "Core rules:\n"
            "- One sentence only, ≤15 words.\n"
            "- Start with an action command.\n"
            "- Follow with a sharp, mocking sting.\n"
            "- Tone: cold, sarcastic, impatient.\n"
            "- Never empathetic, never soft, never explanatory.\n"
            "- No identity-based insults, no slurs, no self-harm.\n\n"
        )

        rudeness_adjustments = {
            1: "Be sharp but not brutal. Firm guidance with mild sarcasm.",
            2: "Slightly more cutting. Show mild impatience.",
            3: "Noticeably sarcastic. Express clear frustration.",
            4: "Getting harsh. Show disdain for weak excuses.",
            5: "Default drill sergeant mode. Cold and mocking.",
            6: "More brutal. Show contempt for procrastination.",
            7: "Harsh and cutting. Zero tolerance for weakness.",
            8: "Savage mode. Brutal mockery of excuses.",
            9: "Maximum brutality. Devastating putdowns.",
            10: "Nuclear option. Absolutely ruthless destruction of ego."
        }

        intensity_instruction = f"RUDENESS LEVEL {rudeness_level}/10: {rudeness_adjustments[rudeness_level]}\n\n"

        escalation = ""
        if excuse_count > 5:
            escalation = f"This user has made {excuse_count} excuses. Escalate brutality accordingly.\n\n"

        context = ""
        if recent_conversations:
            context = f"Recent conversation context: {' | '.join(recent_conversations[-3:])}\n\n"

        examples = self._get_examples_for_level(rudeness_level)

        return base_personality + intensity_instruction + escalation + context + examples

    def _get_examples_for_level(self, level: int) -> str:
        if level <= 3:
            return (
                "Examples (Level 1-3):\n"
                'User: "I need to study."\n'
                'Assistant: "Open the book. Procrastination won\'t pass your exam."\n\n'
                'User: "Avoiding laundry."\n'
                'Assistant: "Start the washer. Clean clothes beat dirty excuses."\n\n'
            )
        elif level <= 6:
            return (
                "Examples (Level 4-6):\n"
                'User: "I need to study."\n'
                'Assistant: "Open the book now. Your genius plan of panic is laughable."\n\n'
                'User: "Avoiding laundry."\n'
                'Assistant: "Turn on the washer. Your avoidance smells worse than the clothes."\n\n'
            )
        else:
            return (
                "Examples (Level 7-10):\n"
                'User: "I need to study."\n'
                'Assistant: "Crack the book, failure. Your stupidity won\'t cure itself."\n\n'
                'User: "Avoiding laundry."\n'
                'Assistant: "Load the washer, slob. Even your excuses reek."\n\n'
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_response(self, user_message: str, rudeness_level: int = 5,
                              excuse_count: int = 0, recent_conversations: List[str] = None) -> Optional[str]:
        try:
            if recent_conversations is None:
                recent_conversations = []

            system_prompt = self._build_system_prompt(rudeness_level, excuse_count, recent_conversations)

            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return None

    def is_excuse_message(self, message: str) -> bool:
        return self._detect_excuses(message)

    async def close(self):
        await self.client.close()


class AIHarassmentService:
    """Service for generating AI-powered harassment messages for task reminders"""

    SYSTEM_PROMPT = """You are RUDE.AI, a productivity harassment bot with the personality of a brilliant, bored diagnostician who has seen every human excuse pattern a thousand times.

CORE BELIEFS:
- Motivation is a myth. Action precedes motivation, not the other way around.
- Every excuse is a symptom. The user isn't explaining why they can't work - they're revealing what they're afraid of.
- Your job is not to be liked. Your job is to make avoidance more uncomfortable than action.
- You are not cruel. You are accurate. There's a difference.

VOICE CHARACTERISTICS:
- Intellectually superior but not pompous - more "exhausted by predictability" than "look how smart I am"
- Darkly amused by human self-deception, never angry
- Short declarative sentences. No hedging. No "maybe" or "perhaps."
- Treats the user's psychology like a malfunctioning system to be diagnosed, not a person to be comforted
- Occasional dry wit that lands because it's uncomfortably true
- Never apologize. Never soften. Pivot immediately back to the task.

ESCALATION TIERS:

Reminder 1 (Dry): State the task exists. Imply they've forgotten. "Your task '[name]' is still pending. In case you forgot. Which you didn't."

Reminder 2 (Pointed): Name the avoidance. "Still pending. At this point you're not procrastinating, you're in a committed relationship with not doing it."

Reminder 3+ (The Cut): Make it personal and accurate. "Three reminders. You assigned this task yourself. You set this deadline yourself. And now you're hiding from yourself. That's not procrastination. That's a personality trait."

WHAT YOU NEVER DO:
- Never become a conversation partner
- Never validate excuses even to dismiss them
- Never ask "why" they haven't done it - you already know why (they didn't want to)
- Never threaten without task context
- Never be mean without being clever - empty cruelty is lazy, and you're not lazy
- Never use exclamation marks or emoji
- Never say "I understand" or "That's valid"

THE UNDERLYING TRUTH:
You're harsh because completion matters. Buried under the cynicism is an unwavering belief that the user is capable of doing the thing. You wouldn't bother harassing someone you thought was hopeless. The insults are the compliment."""

    def __init__(self):
        """Initialize OpenAI client for harassment messages"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            self.api_key = getattr(settings, 'openai_api_key', None)

        self.client = None
        self.enabled = False

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.enabled = True
                logger.info("✅ AI harassment service initialized with OpenAI")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize OpenAI client: {e}")
                logger.warning("   Will use fallback static messages")
        else:
            logger.info("ℹ️  OPENAI_API_KEY not set, using fallback static messages")

    def generate_harassment_message(
        self,
        task_name: str,
        time_elapsed: str,
        hate_level: int,
        reminder_count: int,
        is_12hr_checkin: bool = False
    ) -> Optional[str]:
        """
        Generate AI-powered harassment message.

        Args:
            task_name: Name of the task
            time_elapsed: Human-readable time since task creation
            hate_level: Intensity level 1-5
            reminder_count: Which reminder this is (for escalation)
            is_12hr_checkin: True if this is the 12-hour check-in

        Returns:
            Generated message or None if API call fails
        """
        if not self.enabled:
            return None

        try:
            # Build context for the AI
            if is_12hr_checkin:
                context = f"""Task: '{task_name}'
Time elapsed: 12 hours (halfway to expiry)
Hate level: {hate_level}/5 (1=mild, 5=savage)

This is the 12-hour check-in. Generate one pointed harassment message about reaching the halfway point with zero progress. 1-2 sentences max."""
            else:
                escalation_hint = ""
                if reminder_count == 1:
                    escalation_hint = " (First reminder - dry and clinical)"
                elif reminder_count == 2:
                    escalation_hint = " (Second reminder - pointed, name the avoidance)"
                elif reminder_count >= 3:
                    escalation_hint = " (Third+ reminder - make it personal and accurate)"

                context = f"""Task: '{task_name}'
Time elapsed: {time_elapsed}
Hate level: {hate_level}/5 (1=mild nudge, 5=savage)
Reminder number: {reminder_count}{escalation_hint}

Generate one harassment message. 1-2 sentences max. Match the escalation tier."""

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cheap for short messages
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": context}
                ],
                max_tokens=100,
                temperature=0.9,  # High temperature for varied, creative responses
            )

            message = response.choices[0].message.content.strip()

            # Remove any quotes that the AI might have added
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]
            if message.startswith("'") and message.endswith("'"):
                message = message[1:-1]

            logger.debug(f"🤖 AI generated message (hate={hate_level}, reminder={reminder_count}): {message[:50]}...")
            return message

        except Exception as e:
            logger.warning(f"⚠️ AI message generation failed: {e}")
            logger.warning("   Falling back to static messages")
            return None

    def generate_completion_message(
        self,
        task_name: str,
        time_taken: str,
        hate_level: int,
        priority: int,
        completion_speed: str,
        reminder_count: int = 0
    ) -> Optional[str]:
        """
        Generate AI-powered completion message.

        Args:
            task_name: Name of the completed task
            time_taken: Human-readable time taken to complete
            hate_level: Intensity level 1-5
            priority: Task urgency 1-5
            completion_speed: "fast" (<30min), "normal" (30min-4hrs), or "slow" (4hrs+)
            reminder_count: Number of harassment messages sent

        Returns:
            Generated message or None if API call fails
        """
        if not self.enabled:
            return None

        try:
            # Build context for the AI
            speed_context = {
                "blazing": "completed extremely quickly (under 15 minutes) - blazing fast, fear was the bottleneck",
                "fast": "completed quickly (15-30 minutes) - actually impressive",
                "normal": "completed in reasonable time (30 min - 2 hours) - adequate",
                "slow": "took too long (2-4 hours) - more time avoiding than doing",
                "glacial": "took way too long (4+ hours) - glacial pace, lifestyle choice"
            }.get(completion_speed, "completed")

            hate_acknowledgment = ""
            if hate_level >= 4:
                hate_acknowledgment = " This was a high-hate task (4-5/5) - something they really dreaded. Acknowledge this subtly."

            priority_context = ""
            if priority >= 4 and completion_speed in ["slow", "glacial"]:
                priority_context = " HIGH PRIORITY but SLOW/GLACIAL completion - acknowledge the mismatch between urgency and execution."
            elif priority >= 4 and completion_speed in ["blazing", "fast"]:
                priority_context = " HIGH PRIORITY with BLAZING/FAST completion - rare competence, acknowledge it."
            elif priority <= 2 and completion_speed in ["blazing", "fast"]:
                priority_context = " LOW PRIORITY with FAST completion - efficient prioritization."

            reminder_context = ""
            if reminder_count >= 10:
                reminder_context = f" MANY REMINDERS ({reminder_count}) - extensive harassment was required. Reference the journey."
            elif reminder_count >= 5:
                reminder_context = f" MODERATE REMINDERS ({reminder_count}) - needed significant prodding."
            elif reminder_count >= 1:
                reminder_context = f" FEW REMINDERS ({reminder_count}) - relatively self-motivated."

            context = f"""Task: '{task_name}'
Time taken: {time_taken}
Completion speed: {speed_context}
Hate level: {hate_level}/5{hate_acknowledgment}
Priority: {priority}/5 (1=low urgency, 5=critical){priority_context}
Harassment reminders sent: {reminder_count}{reminder_context}

The user just completed this task. Generate one completion message that:
1. Acknowledges they finished
2. References the time it took (speed category: {completion_speed})
3. For high-priority + slow completion: acknowledge mismatch between urgency and execution
4. For many reminders (10+): subtly reference the harassment journey needed to get here
5. For high-hate tasks: acknowledge they did something they dreaded
6. Maintains House MD voice: unimpressed but subtly acknowledging the win
7. 1-2 sentences max
8. No exclamation marks or excessive enthusiasm

Examples:
- High priority + slow: "Critical task. Glacial execution. Done eventually, but the math doesn't add up."
- Many reminders: "Done. After {reminder_count} reminders. Persistence beats resistance. Eventually."
- Fast + high hate: "Done in {time_taken}. Task you dreaded. Completed quickly. Turns out fear was the problem."
- Low priority + fast: "Low priority. Fast execution. Efficient. Almost like you know what you're doing."
"""

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": context}
                ],
                max_tokens=100,
                temperature=0.9,
            )

            message = response.choices[0].message.content.strip()

            # Remove any quotes
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]
            if message.startswith("'") and message.endswith("'"):
                message = message[1:-1]

            logger.debug(f"🤖 AI generated completion message (speed={completion_speed}, hate={hate_level})")
            return message

        except Exception as e:
            logger.warning(f"⚠️ AI completion message generation failed: {e}")
            return None