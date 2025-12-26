"""Message templates for the RUDE.AI bot"""
import random


class TaskCreationMessages:
    """Messages for task creation flow"""

    # Opening prompts for /new command
    OPENING_PROMPTS = [
        "Fine. What's this task you're avoiding?\n\n(/cancel if you're giving up already)",

        "Another one? Alright, what is it this time?\n\nType it out, or /cancel to surrender.",

        "Hit me. What are you procrastinating on?\n\n/cancel exists if you're already defeated.",

        "Let's hear it. What's haunting your to-do list?\n\nYou can /cancel, but we both know you won't.",

        "Okay, confess. What should you be doing right now?\n\n(/cancel if the guilt is too much)",

        "Back again. What fresh hell is this?\n\nType the task or /cancel to retreat.",

        "You know the drill. Task. Now.\n\n(/cancel if you need an exit)",

        "Let me guess — something you should've done yesterday?\n\nTell me, or /cancel to avoid the truth.",

        "Ah, a new victim. What's the task?\n\n/cancel works, but that's quitting twice in one day.",

        "I was hoping you'd show up. What are we avoiding today?\n\nSpill it, or hit /cancel like always."
    ]

    @classmethod
    def get_random_opening(cls) -> str:
        """Get a random opening prompt for task creation"""
        return random.choice(cls.OPENING_PROMPTS)

    @classmethod
    def get_task_confirmation(cls, task_name: str, priority: int, hate_level: int) -> str:
        """Get a confirmation message based on priority (urgency) and hate level"""

        # Select message based on priority (urgency)
        if priority >= 4:  # High priority (4-5)
            messages = [
                f"📋 {task_name}\nGo. Now. /done when it's done, /list to procrastinate more.",
                f"📋 {task_name}\nMove. Immediately. /done or /list",
                f"📋 {task_name}\nStop reading this. Start doing. /done when finished."
            ]
        elif priority >= 3:  # Medium-high priority (3)
            messages = [
                f"📋 {task_name}\nThis one actually matters. /done or /list",
                f"📋 {task_name}\nGet on it. /done when complete.",
                f"📋 {task_name}\nNot a suggestion. /done or /list"
            ]
        elif priority >= 2:  # Medium priority (2)
            messages = [
                f"📋 {task_name}\nNoted. /done when finished.",
                f"📋 {task_name}\nLogged. /done or /list",
                f"📋 {task_name}\nSure. /done whenever you get to it."
            ]
        else:  # Low priority (1)
            messages = [
                f"📋 {task_name}\nSure. /done whenever.",
                f"📋 {task_name}\nFine. /done or /list",
                f"📋 {task_name}\nAdded. /done when you feel like it."
            ]

        message = random.choice(messages)

        # Add hate level context if high
        if hate_level >= 4:
            message += "\n\nYou clearly despise this task. I'll remind you accordingly."

        return message
