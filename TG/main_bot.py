import asyncio
import sys
from handlers_bot import register_handlers
from loguru import logger
from aiogram import Bot, Dispatcher
from config import config
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode


async def main() -> None:
    # Создание сессии и бота
    session = AiohttpSession()
    bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML), session=session)

    dp = Dispatcher()

    # Регистрация всех обработчиков
    register_handlers(dp)

    logger.info("Бот запущен и готов к работе.")
    try:
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
