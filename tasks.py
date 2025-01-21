from celery_app import celery_app
from database.db import get_db
from database.models import HabitInDB, HabitLogInDB
from sqlalchemy import select
from datetime import datetime
from TG.bot import bot


@celery_app.task
async def send_habit_reminders():

    today = datetime.utcnow().date()

    async with get_db() as session:

        result = await session.execute(
            select(HabitInDB)
            .where(HabitInDB.is_tracked == True)
            .where(~session.query(HabitLogInDB)
                .filter(HabitLogInDB.habit_id == HabitInDB.id, HabitLogInDB.log_date == today).exists())
        )
        habits = result.scalars().all()

        for habit in habits:
            await bot.send_message(
                habit.user_id,  # Отправляем сообщение пользователю с этим ID
                f"⏰ Не забудьте отметить привычку '{habit.name}' за сегодня!"
            )