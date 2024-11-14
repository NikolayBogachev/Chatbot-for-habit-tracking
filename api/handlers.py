import sys
from typing import List

from fastapi.params import Body
from loguru import logger

from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from starlette.responses import JSONResponse

from database.db import AsyncSession, get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from api.pydantic_models import User, HabitCreate, HabitResponse, HabitUpdate, HabitLogResponse, \
    HabitLogCreate
from database.func_db import UserCRUD, HabitCRUD, HabitLogCRUD
from api.auth import AuthService, oauth2_scheme
from config import config
from database.models import HabitInDB

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time} {level} {message}", backtrace=True, diagnose=True)


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

    payload = AuthService.decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await UserCRUD(db).get_user(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(data={"sub": username}, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = AuthService.create_refresh_token(data={"sub": username}, expires_delta=refresh_token_expires)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/habits", response_model=HabitResponse)
async def create_habit(
    habit_data: HabitCreate,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    user_crud = UserCRUD(db)
    logger.info(f"Received token: {token}")

    try:
        current_user = await user_crud.get_current_user(token)
        logger.info(f"Current user: {current_user.id}")

        habit_crud = HabitCRUD(db)
        new_habit = await habit_crud.create_habit(
            user_id=current_user.id,
            name=habit_data.name,
            description=habit_data.description,
            target_days=habit_data.target_days,
            streak_days=habit_data.streak_days,
            start_date=habit_data.start_date,
            last_streak_start=habit_data.last_streak_start,
            current_streak=habit_data.current_streak,
            total_completed=habit_data.total_completed,
            is_tracked=habit_data.is_tracked
        )

        return new_habit

    except HTTPException as http_exc:
        return JSONResponse(
            status_code=http_exc.status_code,
            content={"success": False, "detail": http_exc.detail}
        )

    except SQLAlchemyError as sql_exc:
        logger.error(f"Database error: {sql_exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "detail": "Ошибка базы данных."}
        )

    except Exception as exc:
        logger.error(f"Unexpected error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "detail": "Произошла непредвиденная ошибка."}
        )


@router.get("/habits/{habit_id}", response_model=HabitCreate)
async def get_habit(
        habit_id: int,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):
    user_crud = UserCRUD(db)
    logger.info(f"Received token: {token}")

    current_user = await user_crud.get_current_user(token)

    habit_crud = HabitCRUD(db)
    habit = await habit_crud.get_habit(habit_id)

    if habit is None or habit.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Habit not found or not accessible")

    return habit


@router.get("/habits", response_model=List[HabitResponse])
async def get_habits(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):
    user_crud = UserCRUD(db)
    logger.info(f"Received token: {token}")

    current_user = await user_crud.get_current_user(token)
    logger.info(f"Current user ID: {current_user.id}")

    habit_crud = HabitCRUD(db)
    habits = await habit_crud.get_habits_by_user(current_user.id)

    return habits


@router.put("/habits/{habit_id}", response_model=HabitUpdate)
async def update_habit(
        habit_id: int,
        habit_update: HabitUpdate,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):
    habit_crud = HabitCRUD(db)

    user_crud = UserCRUD(db)
    current_user = await user_crud.get_current_user(token)

    habit = await habit_crud.get_habit(habit_id)
    if habit is None or habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found or access denied")

    updated_habit = await habit_crud.update_habit(
        habit_id=habit_id,
        name=habit_update.name,
        description=habit_update.description,
        target_days=habit_update.target_days,
        streak_days=habit_update.streak_days,
        start_date=habit_update.start_date,
        is_tracked=habit_update.is_tracked
    )

    return updated_habit


@router.delete("/habits/{habit_id}", response_model=None)
async def delete_habit(
        habit_id: int,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):
    habit_crud = HabitCRUD(db)
    user_crud = UserCRUD(db)

    try:
        current_user = await user_crud.get_current_user(token)

        await habit_crud.delete_habit(habit_id)
        return {"detail": "Habit deleted successfully"}

    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"Habit with id {habit_id} not found")


@router.post("/habits/{habit_id}/logs", response_model=HabitLogResponse)
async def create_habit_log(
    habit_id: int,
    log_data: HabitLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """
       Создает запись о выполнении привычки за текущий день.

       - **habit_id** (int): Идентификатор привычки, для которой нужно добавить запись.
       - **completed** (bool): Флаг выполнения привычки (True — выполнено, False — не выполнено).

       Процесс:
       1. Проверяет, существует ли привычка с переданным `habit_id`.
       2. Проверяет, есть ли уже запись за текущий день.
       3. Если запись отсутствует, создает новую запись о выполнении привычки.
       4. Обновляет текущую серию дней выполнения привычки:
           - Если привычка выполнена (completed=True), увеличивает серию и общее количество выполнений.
           - Если не выполнена, сбрасывает серию.

       Возвращает созданную запись о выполнении.

       Пример запроса:
       ```json
       {
         "completed": true
       }
       ```

       Ответ:
       - **201 Created**: Успешно созданная запись.
       - **404 Not Found**: Привычка с указанным `habit_id` не найдена.
       - **400 Bad Request**: Запись о выполнении привычки за текущий день уже существует.
       """

    habit_log_crud = HabitLogCRUD(db)

    habit = await db.get(HabitInDB, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    log_date = datetime.utcnow().date()

    existing_logs = await habit_log_crud.get_habit_logs_by_date(habit_id, log_date)
    if existing_logs:
        raise HTTPException(status_code=400, detail="Log for today already exists")

    new_log = await habit_log_crud.create_habit_log(habit_id, log_date, log_data)

    if log_data.completed:
        habit.current_streak += 1
        habit.total_completed += 1
    else:
        habit.current_streak = 0

    db.add(habit)
    await db.commit()

    await db.refresh(habit)

    return new_log


@router.get("/unlogged_habits", response_model=List[HabitResponse])
async def get_habits(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):
    user_crud = UserCRUD(db)
    logger.info(f"Received token: {token}")

    current_user = await user_crud.get_current_user(token)
    logger.info(f"Current user ID: {current_user.id}")

    habit_crud = HabitCRUD(db)
    habits = await habit_crud.get_unlogged_tracked_habits(current_user.id)

    return habits
