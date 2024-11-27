from datetime import date, datetime
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import UserInDB, HabitInDB, HabitLogInDB
from api.pydantic_models import User, HabitLogCreate
from api.auth import AuthService


class UserCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, username: str) -> Optional[UserInDB]:
        query = select(UserInDB).filter(UserInDB.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_user(self, user: User) -> UserInDB:
        db_user = UserInDB(username=user.username, hashed_password=AuthService.get_password_hash(user.password))

        async with self.db as session:
            try:
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
            except IntegrityError:
                await session.rollback()
                raise HTTPException(status_code=400, detail="User already registered")

        return db_user

    async def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        user = await self.get_user(username)
        if user is None or not AuthService.verify_password(password, user.hashed_password):
            return None
        return user

    async def get_current_user(self, token: str) -> UserInDB:
        payload = AuthService.decode_access_token(token)
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
        user = await self.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user


class HabitCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_unlogged_tracked_habits(self, user_id: int) -> list[HabitInDB]:
        """
        Возвращает список отслеживаемых привычек, которые не были отмечены сегодня.
        """
        today = datetime.utcnow().date()

        statement = select(HabitInDB).filter(
            HabitInDB.user_id == user_id,
            HabitInDB.is_tracked == True
        ).options(selectinload(HabitInDB.logs))

        result = await self.db.execute(statement)
        habits = result.scalars().all()

        unlogged_habits = []

        for habit in habits:

            today_log = next((log for log in habit.logs if log.log_date == today), None)
            if not today_log:
                unlogged_habits.append(habit)

        return unlogged_habits

    async def create_habit(
            self,
            user_id: int,
            name: str,
            description: Optional[str],
            target_days: int,
            streak_days: int,
            start_date: date,
            last_streak_start: Optional[date],
            current_streak: int,
            total_completed: int,
            is_tracked: Optional[bool]
    ) -> HabitInDB:
        new_habit = HabitInDB(
            user_id=user_id,
            name=name,
            description=description,
            target_days=target_days,
            streak_days=streak_days,
            start_date=start_date,
            last_streak_start=last_streak_start,
            current_streak=current_streak,
            total_completed=total_completed,
            is_tracked=is_tracked
        )
        self.db.add(new_habit)
        await self.db.commit()
        await self.db.refresh(new_habit)
        return new_habit

    async def get_habit(self, habit_id: int) -> Optional[HabitInDB]:
        query = select(HabitInDB).filter(HabitInDB.id == habit_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_habits_by_user(self, user_id: int) -> Sequence[HabitInDB]:
        query = select(HabitInDB).filter(HabitInDB.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_habit(self, habit_id: int, name: Optional[str] = None, target_days: Optional[int] = None,
                           streak_days: Optional[int] = None, start_date: Optional[str] = None,
                           description: Optional[str] = None, is_tracked: Optional[bool] = None) -> Optional[HabitInDB]:
        habit = await self.get_habit(habit_id)
        if habit is None:
            raise NoResultFound(f"Habit with id {habit_id} not found.")

        if name is not None:
            habit.name = name
        if target_days is not None:
            habit.target_days = target_days
        if streak_days is not None:
            habit.streak_days = streak_days
        if start_date is not None:
            habit.start_date = start_date
        if description is not None:
            habit.description = description
        if is_tracked is not None:
            habit.is_tracked = is_tracked

        self.db.add(habit)
        await self.db.commit()
        await self.db.refresh(habit)
        return habit

    async def delete_habit(self, habit_id: int) -> None:
        habit = await self.get_habit(habit_id)
        if habit is None:
            raise NoResultFound(f"Habit with id {habit_id} not found.")

        await self.db.delete(habit)
        await self.db.commit()


class HabitLogCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_habit_log(self, habit_id: int, log_date: date, log_data: HabitLogCreate):

        new_log = HabitLogInDB(
            habit_id=habit_id,
            log_date=log_date,
            completed=log_data.completed
        )

        self.db.add(new_log)

        # Коммитим изменения
        await self.db.commit()

        # Обновляем сессию и возвращаем новый лог
        await self.db.refresh(new_log)
        return new_log

    async def get_habit_logs_by_date(self, habit_id: int, log_date: date) -> Sequence[HabitLogInDB]:
        result = await self.db.execute(
            select(HabitLogInDB).where(
                HabitLogInDB.habit_id == habit_id,
                HabitLogInDB.log_date == log_date
            )
        )
        return result.scalars().all()

    async def delete_habit_log(self, log_id: int) -> None:
        # Удаление записи о выполнении привычки
        result = await self.db.execute(select(HabitLogInDB).where(HabitLogInDB.id == log_id))
        log = result.scalars().first()
        if log is None:
            raise NoResultFound(f"Habit log with id {log_id} not found.")
        await self.db.delete(log)
        await self.db.commit()
