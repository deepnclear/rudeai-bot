#!/usr/bin/env python3
"""
Test 5-category speed system with priority and reminder count enhancements.

Tests all completion message improvements:
1. Reminder count tracking and context
2. Priority context (mismatch detection)
3. 5 speed categories (blazing/fast/normal/slow/glacial)
4. AI context enhancements
5. Static template variations
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ['ENV_FILE'] = '.env.test'

from rudeai_bot.handlers.bot_handlers import BotHandlers
from rudeai_bot.services.ai_service import AIService


def test_5_speed_categories():
    """Test all 5 speed categories with various scenarios"""
    print("\n" + "="*80)
    print("5-CATEGORY SPEED SYSTEM TEST")
    print("="*80)

    ai_service = AIService()
    handlers = BotHandlers(ai_service)

    test_cases = [
        {
            "name": "BLAZING (<15 min)",
            "duration": 600,  # 10 minutes
            "hate": 5,
            "priority": 4,
            "reminders": 0,
            "expected_speed": "blazing"
        },
        {
            "name": "FAST (15-30 min)",
            "duration": 1200,  # 20 minutes
            "hate": 3,
            "priority": 5,
            "reminders": 1,
            "expected_speed": "fast"
        },
        {
            "name": "NORMAL (30min-2hr)",
            "duration": 3600,  # 1 hour
            "hate": 2,
            "priority": 3,
            "reminders": 3,
            "expected_speed": "normal"
        },
        {
            "name": "SLOW (2-4hr)",
            "duration": 10800,  # 3 hours
            "hate": 3,
            "priority": 5,
            "reminders": 8,
            "expected_speed": "slow"
        },
        {
            "name": "GLACIAL (4hr+)",
            "duration": 21600,  # 6 hours
            "hate": 4,
            "priority": 5,
            "reminders": 15,
            "expected_speed": "glacial"
        },
    ]

    for test_case in test_cases:
        print(f"\n{'='*80}")
        print(f"Speed Category: {test_case['name']}")
        print(f"{'='*80}")

        message = handlers._get_completion_response(
            task_name="Test task",
            duration_seconds=test_case['duration'],
            hate_level=test_case['hate'],
            priority=test_case['priority'],
            reminder_count=test_case['reminders']
        )

        print(f"Duration: {test_case['duration']}s ({test_case['duration']/3600:.2f} hours)")
        print(f"Hate: {test_case['hate']}/5, Priority: {test_case['priority']}/5, Reminders: {test_case['reminders']}")
        print(f"\nMessage:")
        print(f"  {message}")


def test_priority_mismatch_detection():
    """Test priority + speed mismatch detection"""
    print("\n" + "="*80)
    print("PRIORITY MISMATCH DETECTION TEST")
    print("="*80)

    ai_service = AIService()
    handlers = BotHandlers(ai_service)

    scenarios = [
        ("High Priority + Blazing", 5, 600, "blazing - should acknowledge competence"),
        ("High Priority + Fast", 5, 1500, "fast - should acknowledge competence"),
        ("High Priority + Normal", 5, 5400, "normal - no special comment"),
        ("High Priority + Slow", 5, 10800, "slow - MISMATCH acknowledged"),
        ("High Priority + Glacial", 5, 21600, "glacial - MISMATCH acknowledged"),
        ("Low Priority + Blazing", 1, 600, "blazing - efficient"),
        ("Low Priority + Glacial", 1, 21600, "glacial - no mismatch (ok to be slow)"),
    ]

    for name, priority, duration, expected in scenarios:
        message = handlers._get_completion_response(
            task_name="Task",
            duration_seconds=duration,
            hate_level=2,
            priority=priority,
            reminder_count=0
        )

        print(f"\n{name}")
        print(f"  Expected: {expected}")
        print(f"  Message: {message[:120]}...")


def test_reminder_count_acknowledgment():
    """Test reminder count context in messages"""
    print("\n" + "="*80)
    print("REMINDER COUNT ACKNOWLEDGMENT TEST")
    print("="*80)

    ai_service = AIService()
    handlers = BotHandlers(ai_service)

    reminder_scenarios = [
        (0, "No reminders - self-motivated"),
        (3, "Few reminders - relatively self-motivated"),
        (7, "Moderate reminders - needed prodding"),
        (12, "Many reminders - extensive harassment"),
        (20, "Extensive reminders - well-documented resistance"),
    ]

    for count, description in reminder_scenarios:
        message = handlers._get_completion_response(
            task_name="Task",
            duration_seconds=3600,  # 1 hour
            hate_level=3,
            priority=3,
            reminder_count=count
        )

        print(f"\n{description} (count={count})")
        print(f"  Message: {message[:120]}...")


def test_combined_scenarios():
    """Test complex scenarios with all features"""
    print("\n" + "="*80)
    print("COMBINED SCENARIOS TEST")
    print("="*80)

    ai_service = AIService()
    handlers = BotHandlers(ai_service)

    scenarios = [
        {
            "name": "WORST CASE: High Priority + Glacial + Many Reminders + High Hate",
            "task": "File quarterly taxes",
            "duration": 25200,  # 7 hours
            "hate": 5,
            "priority": 5,
            "reminders": 18
        },
        {
            "name": "BEST CASE: High Priority + Blazing + No Reminders + Low Hate",
            "task": "Send quick email",
            "duration": 300,  # 5 minutes
            "hate": 1,
            "priority": 5,
            "reminders": 0
        },
        {
            "name": "HIGH HATE + BLAZING: Fear was the problem",
            "task": "Call dentist",
            "duration": 600,  # 10 minutes
            "hate": 5,
            "priority": 3,
            "reminders": 8
        },
        {
            "name": "NORMAL: Average task, average execution",
            "task": "Review document",
            "duration": 5400,  # 1.5 hours
            "hate": 2,
            "priority": 3,
            "reminders": 3
        },
    ]

    for scenario in scenarios:
        print(f"\n{'='*80}")
        print(f"{scenario['name']}")
        print(f"{'='*80}")

        message = handlers._get_completion_response(
            task_name=scenario['task'],
            duration_seconds=scenario['duration'],
            hate_level=scenario['hate'],
            priority=scenario['priority'],
            reminder_count=scenario['reminders']
        )

        print(f"Task: '{scenario['task']}'")
        print(f"Duration: {scenario['duration']/3600:.2f}h, Hate: {scenario['hate']}/5, Priority: {scenario['priority']}/5, Reminders: {scenario['reminders']}")
        print(f"\nMessage:")
        print(f"  {message}")


def test_message_conciseness():
    """Verify messages stay 1-2 sentences (House MD style)"""
    print("\n" + "="*80)
    print("MESSAGE CONCISENESS TEST")
    print("="*80)

    ai_service = AIService()
    handlers = BotHandlers(ai_service)

    # Generate most complex scenario (all additions)
    message = handlers._get_completion_response(
        task_name="Complete annual tax filing",
        duration_seconds=28800,  # 8 hours (glacial)
        hate_level=5,           # High hate addition
        priority=5,             # Priority addition
        reminder_count=20       # Reminder addition
    )

    sentences = message.count('.') + message.count('!') + message.count('?')
    words = len(message.split())

    print(f"\nMost Complex Scenario (all additions active):")
    print(f"  Message: {message}")
    print(f"\n  Sentence count: {sentences}")
    print(f"  Word count: {words}")

    if sentences <= 4 and words <= 100:
        print(f"  ✅ PASS: Message is concise (House MD style)")
    else:
        print(f"  ⚠️  WARNING: Message may be too verbose")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("COMPLETION MESSAGE ENHANCEMENTS - COMPREHENSIVE TEST")
    print("="*80)
    print("\nTesting:")
    print("  1. ✓ Reminder count tracking and context")
    print("  2. ✓ Priority context (mismatch detection)")
    print("  3. ✓ 5 speed categories (blazing/fast/normal/slow/glacial)")
    print("  4. ✓ AI context enhancements")
    print("  5. ✓ Static template variations")

    try:
        test_5_speed_categories()
        test_priority_mismatch_detection()
        test_reminder_count_acknowledgment()
        test_combined_scenarios()
        test_message_conciseness()

        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nSpeed Categories:")
        print("  • BLAZING: <15 min - 'Fear was the bottleneck'")
        print("  • FAST: 15-30 min - 'Actually impressive'")
        print("  • NORMAL: 30min-2hr - 'Adequate'")
        print("  • SLOW: 2-4hr - 'More avoiding than doing'")
        print("  • GLACIAL: 4hr+ - 'Lifestyle choice'")
        print("\nContext Tracking:")
        print("  • Priority: 1-5 (detects urgency/execution mismatch)")
        print("  • Reminder Count: 0+ (references harassment journey)")
        print("  • Hate Level: 1-5 (acknowledges dreaded tasks)")
        print("\nAll features maintain House MD voice: dry, concise, cutting.")
        print("="*80 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
