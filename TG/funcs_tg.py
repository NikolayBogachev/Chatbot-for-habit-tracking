from typing import Any, List, Dict

from aiogram.client.session import aiohttp
from aiohttp import ClientResponseError, ClientConnectorError

from config import config

from loguru import logger


class User:
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None

    @classmethod
    async def _make_request(cls, url: str, method: str = "POST", data: dict = None, json_data: dict = None,
                            headers: dict = None) -> dict | None:
        """
        Унифицированный метод для отправки HTTP-запросов.
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(method, url, data=data, json=json_data, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed request to {url}. Status code: {response.status}")
                        return None
            except ClientConnectorError:
                logger.error(f"Connection error: Unable to connect to {url}.")
                return None
            except TimeoutError:
                logger.error(f"Request to {url} timed out.")
                return None
            except ClientResponseError as e:
                logger.error(f"Client response error: {e.status} - {e.message}")
                return None
            except Exception as e:
                logger.error(f"An unexpected error occurred: {str(e)}")
                return None

    @classmethod
    def get_auth_header(cls) -> dict[str, str]:
        """
        Возвращает заголовок Authorization с токеном.
        """
        if cls.access_token and cls.token_type:
            return {"Authorization": f"{cls.token_type} {cls.access_token}"}
        return {}

    @classmethod
    async def get_habits(cls) -> dict | None:
        """
        Метод для получения всех привычек текущего пользователя.
        """

        headers = cls.get_auth_header()
        response = await cls._make_request(f"{config.URL}/habits", method="GET", headers=headers)
        if response:
            return response  # Ожидается, что ответ будет списком привычек
        return None

    @classmethod
    async def delete_habit(cls, habit_id: int) -> dict | None:
        """
        Метод для удаления привычки по идентификатору.
        """

        headers = cls.get_auth_header()
        return await cls._make_request(f"{config.URL}/habits/{habit_id}", method="DELETE", headers=headers)

    @classmethod
    async def create_habit(cls, habit_data: dict) -> dict | None:
        """
        Метод для создания новой привычки через запрос к API.
        """

        headers = {
            "Authorization": f"{cls.token_type} {cls.access_token}",
            "Content-Type": "application/json"
        }
        return await cls._make_request(f"{config.URL}/habits", method="POST", json_data=habit_data, headers=headers)

    @classmethod
    async def register_user(cls, username: str, chat_id: int) -> str | None:
        """
        Регистрирует пользователя и возвращает токен доступа.
        """
        payload = {"username": username, "password": str(chat_id)}
        response = await cls._make_request(f"{config.URL}/register", json_data=payload)
        if response:
            cls.access_token = response.get("access_token")
            cls.token_type = response.get("token_type")
            cls.refresh_token = response.get("refresh_token")
            return cls.access_token
        return None

    @classmethod
    async def authenticate_user(cls, username: str, chat_id: int) -> dict | None:
        """
        Аутентифицирует пользователя и сохраняет токены.
        """
        data = {
            'username': username,
            'password': str(chat_id),
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = await cls._make_request(f"{config.URL}/token", data=data, headers=headers)
        if response:
            cls.access_token = response.get("access_token")
            cls.refresh_token = response.get("refresh_token")
            cls.token_type = response.get("token_type")
            return response
        return None

    @classmethod
    async def refresh_token_tg(cls, refresh_token: str) -> dict | None:
        """
        Обновляет токен доступа и сохраняет новый.
        """
        payload = {"refresh_token": refresh_token}
        response = await cls._make_request(f"{config.URL}/refresh-token", json_data=payload)
        if response:
            cls.access_token = response.get("access_token")
            cls.refresh_token = response.get("refresh_token")
            return response
        return None

