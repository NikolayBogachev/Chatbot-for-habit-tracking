from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает и возвращает постоянную клавиатуру с основными кнопками меню.
    """
    # Создаем кнопки
    kb = [
        [
            KeyboardButton(text="📅 Трекинг выполнения")
        ],
        [
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="📝 Выбор привычек")
        ],
        [
            KeyboardButton(text='ℹ️ О сервисе'),
            KeyboardButton(text="🔔 Настройка оповещений")

        ]
    ]

    # Создаем клавиатуру и добавляем кнопки
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False)

    return keyboard