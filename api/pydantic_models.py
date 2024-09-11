from datetime import date, datetime

from pydantic import BaseModel
from typing import List, Optional


class TunedModel(BaseModel):
    """
    Базовый класс для всех моделей.
    Конфигурация:
    - from_attributes: позволяет создавать модели из словарей атрибутов.
    """

    class Config:
        from_attributes = True


class User(TunedModel):
    username: str
    password: str


class UserInDB(TunedModel):
    username: str


class HabitCreate(TunedModel):
    name: str
    description: Optional[str] = None
    target_days: int = 21
    streak_days: int = 21
    start_date: date
    last_streak_start: Optional[date] = None
    current_streak: int = 0
    total_completed: int = 0


class HabitResponse(TunedModel):
    id: int
    name: str
    description: Optional[str] = None
    target_days: int = 21
    streak_days: int = 21
    start_date: date
    last_streak_start: Optional[date] = None
    current_streak: int = 0
    total_completed: int = 0


class HabitUpdate(TunedModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_days: Optional[int] = None
    streak_days: Optional[int] = None
    start_date: Optional[date] = None


class HabitLogResponse(TunedModel):
    id: int
    habit_id: int
    log_date: date
    completed: bool
    created_at: datetime


class HabitLogCreate(TunedModel):
    completed: bool