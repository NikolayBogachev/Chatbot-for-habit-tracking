from datetime import date, datetime
from typing import Optional, Sequence, List, Any, TypeVar, Generic

from fastapi import HTTPException, status
from sqlalchemy import select, Row, RowMapping
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import UserInDB, HabitInDB, HabitLogInDB, Base
from api.pydantic_models import User, HabitLogCreate
from api.auth import AuthService

ModelType = TypeVar("ModelType", bound=Base)


class BaseCRUD(Generic[ModelType]):
    def __init__(self, model: type(ModelType), db_session: AsyncSession):
        self.model = model
        self.db_session = db_session

    async def create(self, **kwargs) -> ModelType:
        """Создание новой записи"""
        instance = self.model(**kwargs)
        self.db_session.add(instance)
        await self.db_session.commit()
        await self.db_session.refresh(instance)
        return instance

    async def get(self, **kwargs) -> Optional[ModelType]:
        """
        Получает одну запись по произвольным полям.
        Например:
            user = await crud.get(username="john")
            user = await crud.get(id=1)
        """
        stmt = select(self.model).filter_by(**kwargs)
        result = await self.db_session.execute(stmt)

        try:
            return result.scalar_one()
        except NoResultFound:
            return None

    async def filter(self, **kwargs) -> Sequence[Row[Any] | RowMapping | Any]:
        """Фильтрация записей по полям"""
        stmt = select(self.model).filter_by(**kwargs)
        result = await self.db_session.execute(stmt)
        return result.scalars().all()

    async def update(self, **kwargs) -> Optional[ModelType]:
        """
        Обновляет запись по произвольным полям.
        Например:
            await crud.update(id=1, username="new_name")
            await crud.update(email="old@example.com", is_active=False)
        """
        instance = await self.get(**kwargs)
        if not instance:
            return None

        for key, value in kwargs.items():
            setattr(instance, key, value)

        await self.db_session.commit()
        await self.db_session.refresh(instance)
        return instance

    async def delete(self, **kwargs) -> bool:
        """
        Удаляет запись по произвольным полям.
        Например:
            await crud.delete(id=1)
            await crud.delete(username="john")
        """
        instance = await self.get(**kwargs)
        if not instance:
            return False

        await self.db_session.delete(instance)
        await self.db_session.commit()
        return True


class UserCRUD(BaseCRUD[UserInDB]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=UserInDB, db_session=db)


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
