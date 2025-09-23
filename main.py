#!/usr/bin/env python3

import asyncio
from rudeai_bot.bot import RudeAIBot


async def main():
    bot = RudeAIBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())