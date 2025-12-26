# RUDE.AI Bot 🤖

A brutal productivity drill sergeant Telegram bot powered by AI. RUDE.AI doesn't do sympathy—it does results.

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://platform.openai.com/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API-blue.svg)](https://core.telegram.org/bots/api)

## Features

### Task Management with Attitude
- **Dual-Parameter System**: Separate hate level (1-5) from priority (1-5)
  - **Hate Level**: How much you dread the task (affects tone/harassment intensity)
  - **Priority**: How urgent the task is (affects reminder frequency)
- **Smart Scheduling**: Dynamic harassment intervals based on priority
  - Priority 5: Every hour → 1.5 hours
  - Priority 1: Every 4 hours + final reminder
- **24-Hour Expiry**: Tasks auto-delete if not completed

### AI-Powered Harassment
- **House MD Personality**: Dry, sarcastic, brutally honest
- **Context-Aware Messages**: References your avoidance patterns
- **Escalating Tone**: More brutal as reminders accumulate
- **5 Speed Categories**: Completion messages vary by how fast you worked
  - Blazing (<15 min): "Fear was the bottleneck"
  - Fast (15-30 min): "Actually impressive"
  - Normal (30min-2hr): "Adequate"
  - Slow (2-4hr): "More avoiding than doing"
  - Glacial (4hr+): "Lifestyle choice"

### Intelligent Completion Feedback
- **Priority Mismatch Detection**: Calls out when urgency didn't match execution
- **Reminder Count Tracking**: References how much harassment was needed
- **Hate Level Acknowledgment**: Recognizes dreaded tasks completed
- **Personalized Messages**: AI generates unique responses based on:
  - Time taken vs priority level
  - Number of reminders sent
  - Task difficulty (hate level)
  - Completion speed category

### Advanced Features
- **Quiet Hours**: No messages 11pm-7am (delayed to 7am)
- **Collision Prevention**: Messages spaced 15+ minutes apart
- **12-Hour Check-in**: Additional motivation for low-priority tasks
- **Excuse Detection**: AI recognizes procrastination patterns
- **Conversation Context**: Bot remembers recent interactions

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL (production) or SQLite (development)
- Telegram Bot Token ([Get one from @BotFather](https://t.me/botfather))
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/rudeai-bot.git
   cd rudeai-bot
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. **Initialize database**
   ```bash
   alembic upgrade head
   ```

6. **Run the bot**
   ```bash
   python -m rudeai_bot.bot
   ```

## Environment Variables

### Required
```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Database
DATABASE_URL=sqlite:///rudeai_bot.db  # or PostgreSQL URL for production
```

### Optional
```bash
# Webhook (for production)
WEBHOOK_URL=https://yourdomain.com
WEBHOOK_SECRET=your_secret_key

# OpenAI Settings
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=40
OPENAI_TEMPERATURE=0.7

# Scheduler
SCHEDULER_TEST_MODE=false  # Set to true for 240x faster testing
```

## Usage

### Basic Commands

```
/start   - Initialize the bot
/new     - Create a new task
/list    - View active tasks
/done    - Mark a task complete
/cancel  - Cancel task creation
```

### Creating a Task

1. Send `/new`
2. Enter task name (e.g., "File taxes")
3. Choose hate level (1-5): How much you dread it
4. Choose priority (1-5): How urgent it is

**Example**:
```
You: /new
Bot: Fine. What's this task you're avoiding?

You: Call dentist
Bot: How much do you hate "Call dentist"? (1-5)
     1 = Mild discomfort
     5 = Would rather eat glass

You: 5
Bot: Priority? (1-5)
     1 = Whenever
     5 = Urgent, do it now

You: 4
Bot: 📋 Call dentist
     Critical task, fast execution. /done or /list
```

### Completing a Task

```
You: /done
Bot: ✓ Call dentist

     Done in 12 minutes. Blazing fast. The task you dreaded took
     less than a coffee break. Fear was clearly the bottleneck.
```

## How It Works

### Scheduling Algorithm

**Priority determines frequency** (how often you get harassed):
- Priority 5: Hourly reminders → 1.5hr after 4 hours
- Priority 4: 1.5hr → 2hr after 4 hours
- Priority 3: 2hr → 3hr after 4 hours
- Priority 2: 3hr → 4hr after 4 hours
- Priority 1: 4hr intervals + 12hr check-in + final reminder

**Hate level determines tone** (how brutal the messages are):
- Hate 1-3: Firm but not brutal
- Hate 4-5: Savage, no mercy

**Special Features**:
- First message: 20 minutes after creation
- Quiet hours: 11pm-7am (messages delayed to 7am)
- Collision prevention: 15-minute minimum spacing
- Expiry: 24 hours (auto-delete if incomplete)

### AI Message Generation

**Harassment Messages**:
```python
System Prompt: House MD personality
Temperature: 0.9 (high variance)
Context:
  - Task name
  - Time elapsed
  - Hate level
  - Reminder count (for escalation)
```

**Completion Messages**:
```python
Context:
  - Task name
  - Time taken
  - Speed category (blazing/fast/normal/slow/glacial)
  - Hate level
  - Priority (for mismatch detection)
  - Reminder count (harassment journey)
```

## Testing

### Test Mode
Enable 240x faster intervals for testing:
```bash
SCHEDULER_TEST_MODE=true python -m rudeai_bot.bot
```

With test mode:
- 20 minutes → 5 seconds
- 1 hour → 15 seconds
- 24 hours → 6 minutes

### Run Tests
```bash
# Scheduler implementation
python test_scheduler_implementation.py

# Completion messages
python test_completion_messages.py

# 5-category speed system
python test_5_speed_categories.py
```

## Deployment

### Railway (Recommended)
```bash
# One-command deploy
./deploy_railway.sh
```

See [Railway Deployment Guide](docs/railway_deployment.md) for details.

### Render
```bash
./deploy_render.sh
```

See [Render Deployment Guide](RENDER_DEPLOYMENT.md) for details.

### Manual Deployment

1. Set environment variables on your platform
2. Set `DATABASE_URL` to PostgreSQL connection string
3. Run migrations: `alembic upgrade head`
4. Start bot: `python -m rudeai_bot.bot`

## Architecture

```
rudeai_bot/
├── bot.py                    # Main entry point
├── config/
│   └── settings.py          # Configuration management
├── database/
│   ├── base.py              # Database setup
│   └── operations.py        # CRUD operations
├── handlers/
│   ├── bot_handlers.py      # Command handlers
│   └── messages.py          # Message templates
├── models/
│   ├── __init__.py
│   ├── user.py              # User model
│   └── task.py              # Task model
├── services/
│   ├── ai_service.py        # OpenAI integration
│   ├── harassment_messages.py  # Message pools
│   └── scheduler_service.py    # APScheduler integration
└── webhook_server.py        # FastAPI webhook server
```

## Technologies

- **Python 3.9+**: Core language
- **python-telegram-bot 21.5**: Telegram Bot API wrapper
- **OpenAI API**: GPT-4o-mini for message generation
- **APScheduler**: Task scheduling and reminders
- **SQLAlchemy**: Database ORM
- **Alembic**: Database migrations
- **FastAPI**: Webhook server (production)
- **PostgreSQL**: Production database
- **SQLite**: Development/testing database

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python test_*.py`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - See [LICENSE](LICENSE) file for details

## Acknowledgments

- Inspired by the "House MD" personality - brutally honest, darkly amused, intellectually superior
- Built for people who need tough love to get things done
- No sympathy. No excuses. Just results.

---

**Warning**: This bot is intentionally rude. If you need encouragement and validation, this is not the bot for you. If you need someone to call out your procrastination and make avoidance more uncomfortable than action, welcome aboard.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/rudeai-bot/issues)
- **Questions**: Open a discussion in the repository
- **Security**: Report vulnerabilities privately to [your-email@example.com]

---

Made with ❤️ (and a lot of sarcasm) by [Your Name]
