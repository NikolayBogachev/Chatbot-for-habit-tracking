from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from database.models import UserInDB, HabitInDB
from api.pydantic_models import User
from api.auth import AuthService


class UserCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, username: str) -> Optional[UserInDB]:
        query = select(UserInDB).filter(UserInDB.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_user(self, user: User) -> UserInDB:
        db_user = UserInDB(username=user.username, hashed_password=get_password_hash(user.password))

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

    async def create_habit(self, user_id: int, title: str, description: Optional[str], duration_days: int):
        new_habit = Habit(
            user_id=user_id,
            title=title,
            description=description,
            duration_days=duration_days,
            current_streak=0,  # Инициализируем текущую серию выполнений
            best_streak=0,     # Лучший результат по серии выполнений
            completed_days=0   # Количество выполненных дней
        )
        self.db.add(new_habit)
        await self.db.commit()
        await self.db.refresh(new_habit)
        return new_habit

    async def get_habit(self, habit_id: int) -> Optional[HabitInDB]:
        query = select(HabitInDB).filter(HabitInDB.id == habit_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_habits_by_user(self, user_id: int) -> List[HabitInDB]:
        query = select(HabitInDB).filter(HabitInDB.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_habit(self, habit_id: int, name: Optional[str] = None, target_days: Optional[int] = None,
                           streak_days: Optional[int] = None, start_date: Optional[str] = None) -> Optional[HabitInDB]:
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