import asyncio
import sys

from loguru import logger

from config import config
from funcs import main

if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time} - {level} - {message}")

    if not config.TOKEN:
        logger.error("BOT_TOKEN не указан. Пожалуйста, установите переменную окружения BOT_TOKEN.")
        sys.exit(1)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
