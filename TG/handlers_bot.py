from aiogram import Dispatcher, html
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger


def register_handlers(dp: Dispatcher):
    @dp.message(CommandStart())
    async def command_start_handler(message: Message) -> None:
        """
        Обработчик команды `/start`
        """
        user_full_name = message.from_user.full_name
        logger.info(f"Пользователь {user_full_name} начал взаимодействие с ботом.")
        await message.answer(f"Привет, {html.bold(user_full_name)}!")

