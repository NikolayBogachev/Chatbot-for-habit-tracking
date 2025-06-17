import asyncio
import sys

from TG.bot import dp, bot

from loguru import logger

from TG.handlers_bot import router
from config import config


async def main() -> None:

    # Регистрация всех обработчиков
    logger.info("Бот запущен и готов к работе.")
    try:
        dp.include_router(router)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Сессия бота закрыта.")

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
