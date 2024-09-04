from aiogram import Dispatcher, html
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger

from TG.funcs import register_user


def register_handlers(dp: Dispatcher):
    @dp.message(CommandStart())
    async def command_start_handler(message: Message):
        user = message.from_user
        access_token = await register_user(user.username, message.chat.id)
        if access_token:
            await message.answer(f"Вы успешно зарегистрированы! Ваш токен: {access_token}")
            logger.info(f"User {user.full_name} registered with token.")
        else:
            await message.answer("Регистрация не удалась. Попробуйте снова позже.")
            logger.error(f"User {user.full_name} registration failed.")

