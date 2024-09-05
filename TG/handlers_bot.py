from aiogram import Dispatcher, html
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger

from TG.funcs_tg import User


def register_handlers(dp: Dispatcher):
    @dp.message(CommandStart())
    async def command_start_handler(message: Message):
        user = message.from_user
        username = user.username
        chat_id = message.chat.id

        # Попытка аутентификации пользователя
        access_token = await User.authenticate_user(username, chat_id)

        if access_token:
            await message.answer(f"Добро пожаловать обратно, {user.full_name}!")
            logger.info(f"User {user.full_name} successfully authenticated.")
        else:
            # Если аутентификация не удалась, регистрируем нового пользователя
            access_token = await User.register_user(username, chat_id)
            if access_token:
                await message.answer(f"Вы успешно зарегистрированы!")
                logger.info(f"User {user.full_name} registered with token.")
            else:
                await message.answer("Регистрация не удалась. Попробуйте снова позже.")
                logger.error(f"User {user.full_name} registration failed.")
