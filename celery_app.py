from celery.app import Celery
from celery.schedules import crontab

celery_app = Celery(
    "habit_reminder",
    broker="redis://localhost:6379/0",  # Настройте на ваш Redis URL
    backend="redis://localhost:6379/0"  # Настройте на ваш Redis URL
)

celery_app.conf.beat_schedule = {
    "send-habit-reminders-everyday": {
        "task": "tasks.send_habit_reminders",
        "schedule": crontab("0", "20"),  # Выполнение каждый день в 20:00 UTC
    },
}
celery_app.conf.timezone = 'UTC'
celery_app.conf.worker_pool = "threads"
