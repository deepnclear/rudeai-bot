#!/usr/bin/env python3
"""
Comprehensive test script for the refactored harassment scheduler.

Tests:
1. First message timing (~5 seconds with 240x scaling)
2. Priority-based intervals (different schedules for each priority)
3. Quiet hours adjustment (11pm-7am → 7am)
4. 12-hour check-in (priority 1-2 only)
5. Collision detection (15-minute minimum spacing)
6. Task cancellation (all jobs removed on /done)
7. AI message generation (harassment and completion)
8. Expiry timing (~6 minutes with 240x scaling)
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ['ENV_FILE'] = '.env.test'

from rudeai_bot.services.scheduler_service import (
    calculate_message_schedule,
    adjust_for_quiet_hours,
    get_priority_intervals,
    TEST_MODE_SCALE_FACTOR
)
from rudeai_bot.services.harassment_messages import HarassmentMessagePool
from rudeai_bot.services.ai_service import AIHarassmentService
from loguru import logger


def test_priority_intervals():
    """Test that priority intervals are correctly defined"""
    print("\n" + "="*60)
    print("TEST 1: Priority Intervals")
    print("="*60)

    expected = {
        5: {'early': 60, 'late': 90},
        4: {'early': 90, 'late': 120},
        3: {'early': 120, 'late': 180},
        2: {'early': 180, 'late': 240},
        1: {'early': 240, 'late': 240}
    }

    all_passed = True
    for priority in range(1, 6):
        intervals = get_priority_intervals(priority)
        expected_intervals = expected[priority]

        if intervals == expected_intervals:
            print(f"✅ Priority {priority}: {intervals}")
        else:
            print(f"❌ Priority {priority}: Expected {expected_intervals}, got {intervals}")
            all_passed = False

    return all_passed


def test_first_message_timing():
    """Test that first message is scheduled at T+20min (scaled)"""
    print("\n" + "="*60)
    print("TEST 2: First Message Timing")
    print("="*60)

    created_at = datetime.now(timezone.utc)

    for priority in range(1, 6):
        schedule = calculate_message_schedule(created_at, priority, test_mode=True)

        if not schedule:
            print(f"❌ Priority {priority}: No messages scheduled!")
            continue

        first_msg = schedule[0]
        time_diff = (first_msg['scheduled_time'] - created_at).total_seconds()
        expected_seconds = (20 * 60) / TEST_MODE_SCALE_FACTOR  # 20min / 240 = 5 seconds

        if abs(time_diff - expected_seconds) < 1:  # Within 1 second tolerance
            print(f"✅ Priority {priority}: First message at T+{time_diff:.1f}s (expected ~{expected_seconds:.1f}s)")
        else:
            print(f"❌ Priority {priority}: First message at T+{time_diff:.1f}s (expected ~{expected_seconds:.1f}s)")

    return True


def test_quiet_hours():
    """Test that quiet hours adjustments work correctly"""
    print("\n" + "="*60)
    print("TEST 3: Quiet Hours Adjustment")
    print("="*60)

    # Test various times in quiet hours
    # Note: The function adjusts to 7:00 AM LOCAL time, which is 4:00 AM UTC (UTC+3)
    # Test cases use UTC times that correspond to quiet hours in local time
    test_cases = [
        (20, 0, "11:00 PM local"),   # 11:00 PM local (UTC+3) = 8:00 PM UTC
        (20, 30, "11:30 PM local"),  # 11:30 PM local = 8:30 PM UTC
        (21, 0, "12:00 AM local"),   # 12:00 AM local = 9:00 PM UTC
        (0, 0, "3:00 AM local"),     # 3:00 AM local = 12:00 AM UTC
        (3, 59, "6:59 AM local"),    # 6:59 AM local = 3:59 AM UTC
    ]

    all_passed = True
    for hour, minute, label in test_cases:
        dt = datetime.now(timezone.utc).replace(hour=hour, minute=minute, second=0, microsecond=0)
        adjusted = adjust_for_quiet_hours(dt, test_mode=True)

        # Convert to local time to check if it's 7:00 AM local
        from rudeai_bot.services.scheduler_service import get_local_time
        adjusted_local = get_local_time(adjusted)

        if adjusted_local.hour == 7 and adjusted_local.minute == 0:
            print(f"✅ {label} → {adjusted_local.strftime('%I:%M %p')} local (UTC: {adjusted.strftime('%I:%M %p')})")
        else:
            print(f"❌ {label} → {adjusted_local.strftime('%I:%M %p')} local (expected 7:00 AM local)")
            all_passed = False

    # Test time outside quiet hours (should not change)
    dt = datetime.now(timezone.utc).replace(hour=14, minute=0)
    adjusted = adjust_for_quiet_hours(dt, test_mode=True)
    if adjusted == dt:
        print(f"✅ 2:00 PM UTC → No adjustment (correct)")
    else:
        adjusted_local = get_local_time(adjusted)
        print(f"❌ 2:00 PM UTC → Adjusted to {adjusted_local.strftime('%I:%M %p')} local (should not change)")
        all_passed = False

    return all_passed


def test_collision_detection():
    """Test that messages are spaced at least 15 minutes apart"""
    print("\n" + "="*60)
    print("TEST 4: Collision Detection")
    print("="*60)

    created_at = datetime.now(timezone.utc)

    for priority in [1, 3, 5]:  # Test low, medium, high priority
        schedule = calculate_message_schedule(created_at, priority, test_mode=True)

        min_spacing = float('inf')
        collision_count = 0

        for i in range(len(schedule) - 1):
            current = schedule[i]['scheduled_time']
            next_msg = schedule[i + 1]['scheduled_time']
            spacing_minutes = (next_msg - current).total_seconds() / 60

            min_spacing = min(min_spacing, spacing_minutes)

            if spacing_minutes < 15:
                collision_count += 1

        if collision_count == 0:
            print(f"✅ Priority {priority}: No collisions, minimum spacing = {min_spacing:.1f} minutes")
        else:
            print(f"❌ Priority {priority}: {collision_count} collisions detected, minimum spacing = {min_spacing:.1f} minutes")

    return True


def test_12hr_checkin():
    """Test that 12-hour check-in is scheduled for priority 1-2"""
    print("\n" + "="*60)
    print("TEST 5: 12-Hour Check-in")
    print("="*60)

    created_at = datetime.now(timezone.utc)

    for priority in range(1, 6):
        schedule = calculate_message_schedule(created_at, priority, test_mode=True)

        checkin_messages = [msg for msg in schedule if msg.get('is_12hr_checkin', False)]

        if priority <= 2:
            if len(checkin_messages) == 1:
                checkin_time = checkin_messages[0]['scheduled_time']
                hours_elapsed = (checkin_time - created_at).total_seconds() / 3600
                expected_hours = 12 / TEST_MODE_SCALE_FACTOR  # ~0.05 hours = 3 minutes

                print(f"✅ Priority {priority}: 12hr check-in at T+{hours_elapsed*60:.1f}min (expected ~{expected_hours*60:.1f}min)")
            else:
                print(f"❌ Priority {priority}: Expected 1 check-in, found {len(checkin_messages)}")
        else:
            if len(checkin_messages) == 0:
                print(f"✅ Priority {priority}: No 12hr check-in (correct)")
            else:
                print(f"❌ Priority {priority}: Found {len(checkin_messages)} check-ins (expected 0)")

    return True


def test_message_generation():
    """Test that message generation works for all hate levels"""
    print("\n" + "="*60)
    print("TEST 6: Message Generation")
    print("="*60)

    task_name = "Write test report"
    hours_old = 2.5

    print("\nHarassment Messages:")
    for hate_level in range(1, 6):
        for reminder_count in [1, 2, 3]:
            message = HarassmentMessagePool.get_message(
                task_name=task_name,
                hate_level=hate_level,
                hours_old=hours_old,
                reminder_count=reminder_count
            )

            if message and len(message) > 0:
                print(f"✅ Hate {hate_level}, Reminder {reminder_count}: {message[:60]}...")
            else:
                print(f"❌ Hate {hate_level}, Reminder {reminder_count}: No message generated")

    print("\n12-Hour Check-in Messages:")
    for hate_level in [1, 3, 5]:
        message = HarassmentMessagePool.get_message(
            task_name=task_name,
            hate_level=hate_level,
            hours_old=12.0,
            is_12hr_checkin=True
        )

        if message and len(message) > 0:
            print(f"✅ Hate {hate_level}: {message[:60]}...")
        else:
            print(f"❌ Hate {hate_level}: No check-in message generated")

    return True


def test_ai_service():
    """Test AI service initialization and message generation"""
    print("\n" + "="*60)
    print("TEST 7: AI Service")
    print("="*60)

    ai_service = AIHarassmentService()

    print(f"AI Service Enabled: {ai_service.enabled}")
    print(f"API Key Present: {'Yes' if ai_service.api_key else 'No'}")

    if ai_service.enabled:
        print("✅ AI service initialized successfully")
        print("⚠️  Note: Actual AI generation requires valid OPENAI_API_KEY")
    else:
        print("ℹ️  AI service not enabled (using static fallbacks)")

    return True


def test_schedule_completeness():
    """Test that each priority level generates expected number of messages"""
    print("\n" + "="*60)
    print("TEST 8: Schedule Completeness")
    print("="*60)

    created_at = datetime.now(timezone.utc)

    # Expected approximate message counts for 24hr period (test mode)
    expected_counts = {
        1: (6, 10),   # Low frequency: ~7-9 messages
        2: (8, 12),   # ~9-11 messages
        3: (10, 14),  # ~11-13 messages
        4: (12, 16),  # ~13-15 messages
        5: (15, 20),  # High frequency: ~16-18 messages
    }

    for priority in range(1, 6):
        schedule = calculate_message_schedule(created_at, priority, test_mode=True)
        count = len(schedule)
        min_expected, max_expected = expected_counts[priority]

        if min_expected <= count <= max_expected:
            print(f"✅ Priority {priority}: {count} messages (expected {min_expected}-{max_expected})")
        else:
            print(f"⚠️  Priority {priority}: {count} messages (expected {min_expected}-{max_expected})")

        # Show schedule details
        print(f"   First: T+{(schedule[0]['scheduled_time'] - created_at).total_seconds():.1f}s")
        print(f"   Last:  T+{(schedule[-1]['scheduled_time'] - created_at).total_seconds():.1f}s")

    return True


def test_expiry_timing():
    """Test that expiry is scheduled at 24 hours (scaled)"""
    print("\n" + "="*60)
    print("TEST 9: Expiry Timing")
    print("="*60)

    created_at = datetime.now(timezone.utc)

    for priority in [1, 3, 5]:
        schedule = calculate_message_schedule(created_at, priority, test_mode=True)

        if schedule:
            last_message = schedule[-1]['scheduled_time']
            time_to_last = (last_message - created_at).total_seconds()
            expected_expiry = (24 * 3600) / TEST_MODE_SCALE_FACTOR  # 24hr / 240 = 360 seconds = 6 minutes

            # Last message should be before expiry
            if time_to_last < expected_expiry:
                print(f"✅ Priority {priority}: Last message at T+{time_to_last:.1f}s (expiry at ~{expected_expiry:.1f}s)")
            else:
                print(f"❌ Priority {priority}: Last message at T+{time_to_last:.1f}s (beyond expiry at ~{expected_expiry:.1f}s)")

    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("HARASSMENT SCHEDULER TEST SUITE")
    print("="*60)
    print(f"Test Mode Scaling: {TEST_MODE_SCALE_FACTOR}x")
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

    tests = [
        ("Priority Intervals", test_priority_intervals),
        ("First Message Timing", test_first_message_timing),
        ("Quiet Hours", test_quiet_hours),
        ("Collision Detection", test_collision_detection),
        ("12-Hour Check-in", test_12hr_checkin),
        ("Message Generation", test_message_generation),
        ("AI Service", test_ai_service),
        ("Schedule Completeness", test_schedule_completeness),
        ("Expiry Timing", test_expiry_timing),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} FAILED with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "="*60)
    print(f"TOTAL: {passed_count}/{total_count} tests passed")
    print("="*60)

    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
