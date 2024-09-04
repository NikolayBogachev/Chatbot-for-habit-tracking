import sys

from loguru import logger
from database.db import AsyncSession, get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from api.pydantic_models import User, UserInDB
from database.func import UserCRUD
from api.auth import create_access_token, verify_password, decode_access_token

logger.remove()  # Удалите все существующие обработчики
logger.add(sys.stdout, level="INFO", format="{time} {level} {message}", backtrace=True, diagnose=True)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()


@router.post("/register")
async def register_user(user: User, db: AsyncSession = Depends(get_db)):
    """
        Регистрация нового пользователя.

        **Параметры**:
        - `user` (User): Объект пользователя, содержащий имя пользователя и пароль.
          Пример тела запроса:
          ```json
          {
              "username": "example_user",
              "password": "example_password"
          }
          ```
        - `db` (AsyncSession): Асинхронная сессия базы данных, предоставляемая через Depends.

        **Возвращает**:
        - `access_token` (str): Токен доступа для зарегистрированного пользователя.
        - `token_type` (str): Тип токена (bearer).

        **Ошибки**:
        - 400: Если пользователь с указанным именем уже зарегистрирован.

        **Описание**:
        Этот эндпоинт используется для регистрации нового пользователя. Если пользователь с указанным именем уже существует,
        будет возвращена ошибка с кодом 400. В случае успешной регистрации создается и возвращается JWT токен,
        который может быть использован для доступа к защищенным ресурсам API.

        **Пример ответа**:
        ```json
        {
            "access_token": "your_jwt_token",
            "token_type": "bearer"
        }
        ```
        """
    user_crud = UserCRUD(db)
    db_user = await user_crud.get_user(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    await user_crud.create_user(user)
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    """
    Авторизация пользователя и получение токена доступа.

    **Параметры**:
    - `form_data` (OAuth2PasswordRequestForm): Форма, содержащая имя пользователя и пароль.
    - `db` (AsyncSession): Асинхронная сессия базы данных, предоставляемая через Depends.

    **Возвращает**:
    - `access_token` (str): Токен доступа для авторизованного пользователя.
    - `token_type` (str): Тип токена (bearer).

    **Ошибки**:
    - 401: Неверное имя пользователя или пароль.

    **Описание**:
    Этот эндпоинт используется для авторизации пользователя. При успешной аутентификации возвращается JWT токен,
    который может быть использован для доступа к защищенным ресурсам API.
    """
    user_crud = UserCRUD(db)

    # Используем метод authenticate_user для проверки учетных данных
    user = await user_crud.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me")
async def read_users_me(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):
    """
    Получение информации о текущем пользователе.

    **Параметры**:
    - `token` (str): JWT токен, предоставляемый через Depends(oauth2_scheme).
      Этот токен используется для идентификации и авторизации текущего пользователя.
    - `db` (AsyncSession): Асинхронная сессия базы данных, предоставляемая через Depends.

    **Возвращает**:
    - `user` (User): Объект пользователя, содержащий информацию о текущем пользователе.

    **Ошибки**:
    - 401: Некорректные учетные данные или истекший токен. Возвращается, если токен не валиден или не может быть декодирован.
    - 404: Пользователь не найден. Возвращается, если декодированный токен содержит имя пользователя, но в базе данных пользователь не найден.

    **Описание**:
    Этот эндпоинт используется для получения информации о текущем пользователе на основе переданного JWT токена.
    Если токен не валиден или пользователь не найден, будет возвращена соответствующая ошибка.

    **Пример ответа**:
    ```json
    {
        "username": "example_user",
        "hashed_password": "hashed_password_value"
    }
    ```
    """
    user_crud = UserCRUD(db)

    # Декодируем токен и получаем полезные данные
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Получаем информацию о пользователе из базы данных
    user = await user_crud.get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user
