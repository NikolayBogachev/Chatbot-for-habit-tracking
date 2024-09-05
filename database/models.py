from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Text,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class UserInDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # Уникальный идентификатор пользователя
    username = Column(String, unique=True, index=True)  # Уникальное имя пользователя
    hashed_password = Column(String)  # Хеш пароля
    created_at = Column(TIMESTAMP, server_default=func.now())  # Дата создания записи пользователя

    habits = relationship("HabitInDB", back_populates="user")  # Связь с привычками


class HabitInDB(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)  # Уникальный идентификатор привычки
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Ссылка на пользователя
    name = Column(String, nullable=False)  # Название привычки
    description = Column(String, nullable=True)  # Описание привычки
    target_days = Column(Integer, nullable=False, default=21)  # Количество дней для прививания привычки
    streak_days = Column(Integer, nullable=False, default=21)  # Количество дней без перерыва
    start_date = Column(Date, nullable=False)  # Дата начала привычки
    last_streak_start = Column(Date)  # Дата начала текущей серии дней без прерыва
    current_streak = Column(Integer, default=0)  # Текущий счетчик дней без перерыва
    total_completed = Column(Integer, default=0)  # Общее количество выполненных дней
    created_at = Column(TIMESTAMP, server_default=func.now())  # Дата создания записи привычки
    updated_at = Column(TIMESTAMP, server_default=func.now(),
                        onupdate=func.now())  # Дата последнего обновления записи привычки

    user = relationship("UserInDB", back_populates="habits")  # Связь с пользователем
    logs = relationship("HabitLogInDB", back_populates="habit")  # Связь с записями о выполнении привычек


class HabitLogInDB(Base):
    __tablename__ = "habit_logs"

    id = Column(Integer, primary_key=True, index=True)  # Уникальный идентификатор записи о выполнении привычки
    habit_id = Column(Integer, ForeignKey('habits.id'), nullable=False)  # Ссылка на привычку
    log_date = Column(Date, nullable=False)  # Дата выполнения или пропуска привычки
    completed = Column(Boolean, nullable=False)  # Флаг, выполнена ли привычка
    created_at = Column(TIMESTAMP, server_default=func.now())  # Дата создания записи

    habit = relationship("HabitInDB", back_populates="logs")  # Связь с привычкой