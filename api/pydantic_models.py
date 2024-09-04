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
