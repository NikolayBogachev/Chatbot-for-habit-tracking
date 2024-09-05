from typing import Any

from aiogram.client.session import aiohttp
from aiohttp import ClientResponseError, ClientConnectorError

from config import config

from loguru import logger


class User:
    @classmethod
    async def register_user(cls, username: str, chat_id: int) -> Any | None:
        """
        Регистрирует пользователя, отправляя запрос на эндпоинт /register и получает токен доступа.

        **Параметры**:
        - `username` (str): Имя пользователя для регистрации.
        - `chat_id` (int): Идентификатор чата, используется как пароль.

        **Возвращает**:
        - `access_token` (str | None): Возвращает токен доступа, если регистрация прошла успешно.
        - `None`: Если регистрация не удалась.

        **Обработка исключений**:
        - Обрабатываются исключения при подключении, таймауты, ошибки ответа сервера и другие сетевые ошибки.

        **Пример использования**:
        ```python
        access_token = await User.register_user("example_username", 12345678)
        if access_token:
            print(f"Access token: {access_token}")
        else:
            print("Registration failed")
        ```
        """
        async with aiohttp.ClientSession() as session:
            try:
                # Формируем данные для отправки
                payload = {"username": username, "password": str(chat_id)}

                # Делаем POST-запрос на эндпоинт /register
                async with session.post(f"{config.URL}/register", json=payload) as response:
                    # Проверяем статус ответа
                    if response.status == 200:
                        data = await response.json()
                        return data.get("access_token")
                    else:
                        logger.error(f"Failed to register user. Status code: {response.status}")
                        return None

            except ClientConnectorError:
                logger.error("Connection error: Unable to connect to the registration server.")
                return None

            except TimeoutError:
                logger.error("Request timed out while trying to register user.")
                return None

            except ClientResponseError as e:
                logger.error(f"Client response error: {e.status} - {e.message}")
                return None

            except Exception as e:
                logger.error(f"An unexpected error occurred: {str(e)}")
                return None

    @classmethod
    async def authenticate_user(cls, username: str, chat_id: int) -> str | None:
        """
        Аутентифицирует пользователя с помощью username и chat_id, обращаясь к эндпоинту `/token`.

        **Параметры**:
        - `username` (str): Имя пользователя.
        - `chat_id` (int): Идентификатор чата, используемый как пароль.

        **Возвращает**:
        - `access_token` (str | None): Токен доступа, если аутентификация прошла успешно, иначе `None`.
        """
        async with aiohttp.ClientSession() as session:
            try:
                # Формируем тело запроса как форму данных (application/x-www-form-urlencoded)
                data = {
                    'username': username,
                    'password': str(chat_id),  # Используем chat_id как пароль
                }

                # Заголовки для формы авторизации
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }

                # Делаем запрос к эндпоинту /token
                async with session.post(f"{config.URL}/token", data=data, headers=headers) as response:
                    if response.status == 200:
                        # Получаем access_token из ответа
                        data = await response.json()
                        return data.get("access_token")
                    else:
                        logger.error(f"Failed to authenticate user. Status: {response.status}")
                        return None

            except ClientResponseError as e:
                logger.error(f"Request error: {e}")
                return None

    @classmethod
    async def refresh_token(cls, refresh_token: str) -> Any | None:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{config.URL}/refresh-token",
                                        json={"refresh_token": refresh_token}) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["access_token"], data["refresh_token"]
                    else:
                        logger.error(f"Failed to refresh token. Status code: {response.status}")
                        return None, None
            except Exception as e:
                logger.error(f"Error occurred while refreshing token: {str(e)}")
                return None, None