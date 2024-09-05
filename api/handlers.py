import sys

from loguru import logger
from database.db import AsyncSession, get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from api.pydantic_models import User, UserInDB
from database.func_db import UserCRUD
from api.auth import AuthService
from config import config

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
    access_token = AuthService.create_access_token(data={"sub": user.username})
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
    access_token = AuthService.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = AuthService.create_refresh_token(data={"sub": user.username}, expires_delta=refresh_token_expires)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh-token")
async def refresh_access_token(
        refresh_token: str = Body(..., embed=True),
        db: AsyncSession = Depends(get_db)
):
    """
    Обновляет access token и refresh token.
    """
    # Декодируем refresh token
    payload = AuthService.decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # Извлекаем username из payload
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Проверяем пользователя в БД
    user = await UserCRUD(db).get_user(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Генерируем новые токены
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(data={"sub": username}, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = AuthService.create_refresh_token(data={"sub": username}, expires_delta=refresh_token_expires)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/habits", response_model=HabitCreate)
async def create_habit(
    habit_data: HabitCreate,
    token: str = Depends(AuthService.get_current_user),  # Проверка JWT токена и получение пользователя
    db: AsyncSession = Depends(get_db)  # Получаем сессию базы данных
):
    user_crud = UserCRUD(db)
    # Проверяем токен и получаем текущего пользователя
    current_user = await user_crud.get_current_user(token)

    # Создаем новую привычку через CRUD
    habit_crud = HabitCRUD(db)
    new_habit = await habit_crud.create_habit(
        user_id=current_user.id,  # Используем id пользователя из токена
        title=habit_data.title,
        description=habit_data.description,
        duration_days=habit_data.duration_days
    )

    return new_habit

