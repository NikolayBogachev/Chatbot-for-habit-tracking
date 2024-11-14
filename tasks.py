from celery_app import celery_app
from database.db import get_db
from database.models import HabitInDB, HabitLogInDB
from sqlalchemy import select
from datetime import datetime
from TG.bot import bot


@celery_app.task
async def send_habit_reminders():
    # Получаем текущее время (дата без времени)
    today = datetime.utcnow().date()

    async with get_db() as session:
        # Находим привычки, которые отслеживаются и не отмечены сегодня
        result = await session.execute(
            select(HabitInDB)
            .where(HabitInDB.is_tracked == True)
            .where(~session.query(HabitLogInDB)
                .filter(HabitLogInDB.habit_id == HabitInDB.id, HabitLogInDB.log_date == today).exists())
        )
        habits = result.scalars().all()

        # Отправляем уведомления пользователям
        for habit in habits:
            await bot.send_message(
                habit.user_id,  # Отправляем сообщение пользователю с этим ID
                f"⏰ Не забудьте отметить привычку '{habit.name}' за сегодня!"
            )