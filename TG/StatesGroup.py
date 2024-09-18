from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery


class HabitStates(StatesGroup):
    waiting_for_description = State()  # Ввода описания привычки
    waiting_for_days = State()  # Ввода количества дней
    useful_habit_submenu = State()
    main_menu = State()  # Главное меню
    useful_habit_menu = State()  # Полезные привычки
    health_menu = State()  # Здоровье
    sport_menu = State()  # Спорт
    nutrition_menu = State()  # Питание
    harmful_habit_menu = State()  # Вредные привычки
    waiting_for_habit_name = State()  # Ввода названия привычки
    update_habits_menu = State()  # Меню обновления привычек


async def switch_keyboard(callback: CallbackQuery, state: FSMContext, next_state: State, keyboard_func):
    # Устанавливаем следующее состояние
    await state.set_state(next_state.state)

    # Заменяем клавиатуру
    await callback.message.edit_reply_markup(reply_markup=keyboard_func())

