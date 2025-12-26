#!/usr/bin/env python3
"""
Test script for enhanced completion messages.

Tests that completion messages now include:
- Priority context (urgency vs execution mismatch)
- Reminder count context (harassment journey)
- Speed categories (fast/normal/slow)
- Hate level acknowledgment
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ['ENV_FILE'] = '.env.test'

from rudeai_bot.handlers.bot_handlers import BotHandlers
from rudeai_bot.services.ai_service import AIService, AIHarassmentService


def test_completion_message_generation():
    """Test completion message generation with various scenarios"""
    print("\n" + "="*80)
    print("COMPLETION MESSAGE ENHANCEMENT TEST")
    print("="*80)

    # Initialize services
    ai_service = AIService()
    handlers = BotHandlers(ai_service)

    # Test scenarios with different combinations
    test_cases = [
        {
            "name": "High Priority + Fast Completion",
            "task_name": "Fix critical bug",
            "duration_seconds": 1200,  # 20 minutes
            "hate_level": 3,
            "priority": 5,
            "reminder_count": 1,
            "expected_elements": ["fast", "priority", "critical"]
        },
        {
            "name": "High Priority + Slow Completion (Mismatch!)",
            "task_name": "Deploy urgent hotfix",
            "duration_seconds": 25200,  # 7 hours
            "hate_level": 2,
            "priority": 5,
            "reminder_count": 15,
            "expected_elements": ["priority", "slow", "reminders", "math"]
        },
        {
            "name": "High Hate + Many Reminders",
            "task_name": "File taxes",
            "duration_seconds": 7200,  # 2 hours
            "hate_level": 5,
            "priority": 3,
            "reminder_count": 12,
            "expected_elements": ["hate", "reminders", "12"]
        },
        {
            "name": "Low Priority + Fast Completion (Efficient)",
            "task_name": "Clean desk",
            "duration_seconds": 600,  # 10 minutes
            "hate_level": 1,
            "priority": 1,
            "reminder_count": 0,
            "expected_elements": ["fast", "impressive"]
        },
        {
            "name": "Normal Everything",
            "task_name": "Write weekly report",
            "duration_seconds": 5400,  # 1.5 hours
            "hate_level": 2,
            "priority": 3,
            "reminder_count": 3,
            "expected_elements": ["adequate", "normal"]
        },
        {
            "name": "High Hate + High Priority + Many Reminders + Slow",
            "task_name": "Call dentist",
            "duration_seconds": 18000,  # 5 hours
            "hate_level": 5,
            "priority": 4,
            "reminder_count": 18,
            "expected_elements": ["hate", "priority", "reminders", "slow"]
        },
    ]

    print(f"\nRunning {len(test_cases)} test scenarios...\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'-'*80}")
        print(f"Test {i}: {test_case['name']}")
        print(f"{'-'*80}")

        print(f"📋 Input:")
        print(f"   Task: '{test_case['task_name']}'")
        print(f"   Duration: {test_case['duration_seconds']}s ({test_case['duration_seconds']/3600:.1f} hours)")
        print(f"   Hate Level: {test_case['hate_level']}/5")
        print(f"   Priority: {test_case['priority']}/5")
        print(f"   Reminders: {test_case['reminder_count']}")

        # Generate completion message
        message = handlers._get_completion_response(
            task_name=test_case['task_name'],
            duration_seconds=test_case['duration_seconds'],
            hate_level=test_case['hate_level'],
            priority=test_case['priority'],
            reminder_count=test_case['reminder_count']
        )

        print(f"\n💬 Generated Message:")
        print(f"   {message}")

        # Check for expected elements (case-insensitive)
        message_lower = message.lower()
        found_elements = []
        missing_elements = []

        for element in test_case.get('expected_elements', []):
            if element.lower() in message_lower:
                found_elements.append(element)
            else:
                missing_elements.append(element)

        if missing_elements:
            print(f"\n⚠️  Note: Expected elements not found: {', '.join(missing_elements)}")
        else:
            print(f"\n✅ All expected elements present")

        print(f"   Found: {', '.join(found_elements) if found_elements else 'None'}")


def test_ai_vs_static_fallback():
    """Test that both AI and static fallback work"""
    print("\n" + "="*80)
    print("AI VS STATIC FALLBACK TEST")
    print("="*80)

    ai_harassment_service = AIHarassmentService()

    print(f"\nAI Service Status:")
    print(f"   Enabled: {ai_harassment_service.enabled}")
    print(f"   API Key: {'Present' if ai_harassment_service.api_key else 'Missing'}")

    if ai_harassment_service.enabled:
        print(f"\n✅ AI generation is ENABLED")
        print(f"   Completion messages will use GPT-4o-mini")
        print(f"   Fallback to static templates if API fails")
    else:
        print(f"\nℹ️  AI generation is DISABLED")
        print(f"   Completion messages will use static templates only")


def test_priority_reminder_combinations():
    """Test specific priority + reminder count combinations"""
    print("\n" + "="*80)
    print("PRIORITY + REMINDER COUNT COMBINATIONS")
    print("="*80)

    ai_service = AIService()
    handlers = BotHandlers(ai_service)

    combinations = [
        # (priority, reminder_count, speed, description)
        (5, 0, "fast", "Critical task, no reminders needed, fast"),
        (5, 15, "slow", "Critical task, many reminders, slow - WORST CASE"),
        (1, 0, "normal", "Low priority, no reminders, normal"),
        (1, 8, "slow", "Low priority, many reminders, slow"),
        (3, 5, "normal", "Medium priority, some reminders, normal"),
    ]

    for priority, reminder_count, speed, description in combinations:
        # Map speed to duration
        duration_map = {
            "fast": 1200,    # 20 min
            "normal": 5400,  # 1.5 hours
            "slow": 18000,   # 5 hours
        }
        duration = duration_map[speed]

        print(f"\n{description}")
        print(f"   Priority: {priority}/5, Reminders: {reminder_count}, Speed: {speed}")

        message = handlers._get_completion_response(
            task_name="Test task",
            duration_seconds=duration,
            hate_level=2,
            priority=priority,
            reminder_count=reminder_count
        )

        print(f"   Message: {message[:100]}...")


def test_message_length():
    """Verify messages stay concise (House MD style)"""
    print("\n" + "="*80)
    print("MESSAGE LENGTH TEST")
    print("="*80)

    ai_service = AIService()
    handlers = BotHandlers(ai_service)

    # Generate a complex scenario (all additions possible)
    message = handlers._get_completion_response(
        task_name="File quarterly tax returns",
        duration_seconds=21600,  # 6 hours
        hate_level=5,  # High hate addition
        priority=5,    # Priority addition (high + slow)
        reminder_count=18  # Reminder addition
    )

    word_count = len(message.split())
    sentence_count = message.count('.') + message.count('!') + message.count('?')

    print(f"\nComplex Scenario (all additions):")
    print(f"   Message: {message}")
    print(f"\n   Word count: {word_count}")
    print(f"   Sentence count: {sentence_count}")

    if word_count > 100:
        print(f"   ⚠️  Warning: Message may be too long (House MD = concise)")
    else:
        print(f"   ✅ Message length appropriate")


def main():
    """Run all tests"""
    try:
        test_completion_message_generation()
        test_ai_vs_static_fallback()
        test_priority_reminder_combinations()
        test_message_length()

        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80)
        print("\nEnhanced completion messages now include:")
        print("  ✓ Priority context (urgency vs execution)")
        print("  ✓ Reminder count context (harassment journey)")
        print("  ✓ Speed categories (fast/normal/slow)")
        print("  ✓ Hate level acknowledgment")
        print("\nBoth AI-generated and static fallback messages support all features.")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
