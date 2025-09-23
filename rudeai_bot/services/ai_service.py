import asyncio
import re
from typing import Optional, List
from openai import AsyncOpenAI
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