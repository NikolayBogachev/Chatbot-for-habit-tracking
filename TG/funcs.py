from typing import Any

from aiogram.client.session import aiohttp

from config import config

from loguru import logger


async def register_user(username: str, chat_id: int) -> Any | None:
    async with aiohttp.ClientSession() as session:
        print(username, chat_id)
        async with session.post(f"http://localhost:8000/register",
                                json={"username": username, "password": f"{chat_id}"}) as response:
            if response.status == 200:
                data = await response.json()
                return data["access_token"]
            else:
                logger.error("Failed to register user")
                return None
