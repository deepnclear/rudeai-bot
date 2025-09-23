from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="rudeai-bot",
    version="1.0.0",
    description="RUDE.AI - A brutal productivity drill sergeant Telegram bot",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "rudeai-bot=rudeai_bot.bot:main",
        ],
    },
)