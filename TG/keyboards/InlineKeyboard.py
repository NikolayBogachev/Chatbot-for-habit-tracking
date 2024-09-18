from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_habit_choice_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="➕ Добавить полезную привычку",
                              callback_data="useful")],
        [InlineKeyboardButton(text="❌ Отказаться от вредной привычки",
                              callback_data="harmful")],
        [InlineKeyboardButton(text="🔍 Отслеживание привычек",
                              callback_data="track")],
        [InlineKeyboardButton(text="⚙️ Редактировать привычки",
                              callback_data="update_habits")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)

    return keyboard


def update_habits_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="✏️  Изменить привычку", callback_data="change")],
        [InlineKeyboardButton(text="❌  Удалить привычку", callback_data="delete")],

    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)

    return keyboard


def useful_habit_choice_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="💪 Здоровье", callback_data="health")],
        [InlineKeyboardButton(text="🏃 Спорт", callback_data="sport")],
        [InlineKeyboardButton(text="🍏 Питание", callback_data="nutrition")],
        [InlineKeyboardButton(text="✍️ Свой вариант", callback_data="option")],
        [InlineKeyboardButton(text="🔄 Назад", callback_data="back")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)

    return keyboard


def health_habit_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="😴 Сон", callback_data="sleep")],
        [InlineKeyboardButton(text="💧 Гидратация", callback_data="hydration")],
        [InlineKeyboardButton(text="🧘‍♀️ Медитация", callback_data="meditation")],
        [InlineKeyboardButton(text="✍️ Свой вариант", callback_data="option")],
        [InlineKeyboardButton(text="🔄 Назад", callback_data="back")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    return keyboard


def sport_habit_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="🏋️‍♂️ Силовые тренировки", callback_data="strength_training")],
        [InlineKeyboardButton(text="🏃 Бег", callback_data="running")],
        [InlineKeyboardButton(text="🏊 Плавание", callback_data="swimming")],
        [InlineKeyboardButton(text="✍️ Свой вариант", callback_data="option")],
        [InlineKeyboardButton(text="🔄 Назад", callback_data="back")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    return keyboard


def nutrition_habit_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="🥗 Овощи и фрукты", callback_data="fruits_veggies")],
        [InlineKeyboardButton(text="🍳 Завтрак", callback_data="breakfast")],
        [InlineKeyboardButton(text="🥤 Снижение сахара", callback_data="less_sugar")],
        [InlineKeyboardButton(text="✍️ Свой вариант", callback_data="option")],
        [InlineKeyboardButton(text="🔄 Назад", callback_data="back")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    return keyboard


def harmful_habit_choice_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="🚬 Курение", callback_data="smoking")],
        [InlineKeyboardButton(text="🍺 Алкоголь", callback_data="alcohol")],
        [InlineKeyboardButton(text="✍️ Свой вариант", callback_data="option")],
        [InlineKeyboardButton(text="🔄 Назад", callback_data="back")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)

    return keyboard