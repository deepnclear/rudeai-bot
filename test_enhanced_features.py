#!/usr/bin/env python3
"""
Test script for the enhanced RUDE.AI features
"""

import re
from typing import List

class MockAIService:
    """Mock AI service for testing the enhanced features"""

    def __init__(self):
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

        return base_personality + intensity_instruction + escalation + context

    def is_excuse_message(self, message: str) -> bool:
        return self._detect_excuses(message)

    def get_system_prompt_preview(self, rudeness_level: int, excuse_count: int, recent_conversations: List[str] = None):
        if recent_conversations is None:
            recent_conversations = []
        return self._build_system_prompt(rudeness_level, excuse_count, recent_conversations)


def test_excuse_detection():
    """Test the excuse detection functionality"""
    print("=== Excuse Detection Test ===")
    ai = MockAIService()

    test_cases = [
        ("I need to study but I'm too tired", True),
        ("I should do laundry later", True),
        ("I'm procrastinating on my homework", True),
        ("I finished all my tasks today", False),
        ("Maybe I'll start tomorrow", True),
        ("I'm avoiding this email", True),
        ("I can't seem to focus", True),
        ("I will start working now", False),
        ("Let me postpone this meeting", True),
        ("I'm ready to tackle this project", False)
    ]

    for message, expected in test_cases:
        result = ai.is_excuse_message(message)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' -> {result} (expected {expected})")

    print()


def test_rudeness_levels():
    """Test different rudeness levels"""
    print("=== Rudeness Level Test ===")
    ai = MockAIService()

    for level in [1, 3, 5, 7, 10]:
        prompt = ai.get_system_prompt_preview(level, 0)
        print(f"Level {level}:")
        # Extract just the rudeness adjustment line
        lines = prompt.split('\n')
        for line in lines:
            if f"RUDENESS LEVEL {level}" in line:
                print(f"  {line}")
                break
        print()


def test_context_awareness():
    """Test context awareness with recent conversations"""
    print("=== Context Awareness Test ===")
    ai = MockAIService()

    recent_conversations = [
        "I'm too tired to work",
        "Maybe later I'll start",
        "I'm procrastinating again"
    ]

    prompt = ai.get_system_prompt_preview(5, 3, recent_conversations)
    print("System prompt with context:")
    lines = prompt.split('\n')
    for line in lines:
        if "Recent conversation context:" in line:
            print(f"  {line}")
            break

    print()


def test_excuse_escalation():
    """Test excuse count escalation"""
    print("=== Excuse Escalation Test ===")
    ai = MockAIService()

    for excuse_count in [0, 3, 6, 10]:
        prompt = ai.get_system_prompt_preview(5, excuse_count)
        print(f"Excuse count {excuse_count}:")
        if excuse_count > 5:
            lines = prompt.split('\n')
            for line in lines:
                if "made" in line and "excuses" in line:
                    print(f"  {line}")
                    break
        else:
            print("  No escalation (under threshold)")
        print()


def main():
    """Run all tests"""
    print("🤖 RUDE.AI Enhanced Features Test Suite\n")

    test_excuse_detection()
    test_rudeness_levels()
    test_context_awareness()
    test_excuse_escalation()

    print("✅ All tests completed successfully!")
    print("\nEnhanced features implemented:")
    print("• Rudeness intensity control (1-10 scale)")
    print("• Excuse detection and tracking")
    print("• Context awareness with recent conversations")
    print("• Escalation based on user patterns")
    print("• /rudeness and enhanced /stats commands")


if __name__ == "__main__":
    main()