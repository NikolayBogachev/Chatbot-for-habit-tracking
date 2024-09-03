from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from config import config
from handlers_bot import register_handlers
from loguru import logger


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
