#!/usr/bin/env python3
"""
Webhook server entry point for RUDE.AI Bot
"""

import asyncio
import sys
from rudeai_bot.webhook_server import webhook_server


async def main():
    """Main entry point for webhook server"""
    try:
        await webhook_server.startup()

        # Keep the server running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived interrupt signal, shutting down...")
    except Exception as e:
        print(f"Error running webhook server: {e}")
        sys.exit(1)
    finally:
        await webhook_server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())