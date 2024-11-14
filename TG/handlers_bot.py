
from aiogram import F, Router

from aiogram.filters import CommandStart, StateFilter

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ForceReply

from loguru import logger


from TG.StatesGroup import HabitStates, switch_keyboard
from TG.bot import bot
from TG.funcs_tg import User
from TG.keyboards.InlineKeyboard import (get_habit_choice_keyboard, useful_habit_choice_keyboard,
                                         harmful_habit_choice_keyboard, health_habit_keyboard, sport_habit_keyboard,
                                         nutrition_habit_keyboard, update_habits_keyboard,
                                         create_habits_inline_keyboard, create_change_fields_keyboard,
                                         track_habit_keyboard, create_track_habits_inline_keyboard,
                                         completion_marks_keyboard)
from TG.keyboards.ReplyKeyboard import get_main_menu_keyboard

router = Router()

user_messages = {}
"""
Блок основного меню.
"""


@router.message(CommandStart())
async def command_start_handler(message: Message):
    user = message.from_user
    username = user.username
    chat_id = message.chat.id

    auth_response = await User.authenticate_user(username, chat_id)
    logger.debug(f"Auth response: {auth_response}")

    if auth_response:
        # Сохранение токенов после успешной аутентификации
        User.access_token = auth_response.get("access_token")
        User.refresh_token = auth_response.get("refresh_token")
        User.token_type = auth_response.get("token_type")

        await message.answer(f"Добро пожаловать обратно, {user.full_name}!",
                             reply_markup=get_main_menu_keyboard())
        logger.info(f"User {user.full_name} successfully authenticated.")
    else:
        # Если аутентификация не удалась, регистрируем нового пользователя
        reg_response = await User.register_user(username, chat_id)
        logger.debug(f"Registration response: {reg_response}")

        if reg_response:
            # Сохранение токенов после успешной регистрации
            User.access_token = reg_response
            User.refresh_token = None
            User.token_type = "Bearer"
            await message.answer(f"Вы успешно зарегистрированы!",
                                 reply_markup=get_main_menu_keyboard())
            logger.info(f"User {user.full_name} registered with token.")
        else:
            await message.answer("Регистрация не удалась. Попробуйте снова позже.")
            logger.error(f"User {user.full_name} registration failed.")


@router.message(lambda message: message.text == "📝 Выбор привычек")
async def handle_habit_choice(message: Message, state: FSMContext):

    await message.delete()
    await state.set_state(HabitStates.main_menu)

    await bot.send_message(
        chat_id=message.chat.id,
        text="Выберите действие:",
        reply_markup=get_habit_choice_keyboard()
    )


@router.callback_query(F.data == "cancel", StateFilter(HabitStates.main_menu, HabitStates.execution))
async def handle_cancel(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()

    await state.clear()

"""
Блок получения статстики.
"""


@router.message(lambda message: message.text == "📊 Статистика")
async def handle_habit_choice(message: Message, state: FSMContext):
    await message.delete()
    await state.set_state(HabitStates.statistics)

    if not (habits := await User.get_habits()):
        await User.authenticate_user(message.from_user.username, message.chat.id)
        habits = await User.get_habits()

    if habits:
        tracked_habits = [habit for habit in habits if habit.is_tracked == True]

        if not tracked_habits:
            await message.answer("У вас нет отслеживаемых привычек.")
            return

        stats_message = "📊 Ваша статистика по привычкам:\n\n"

        for habit in tracked_habits:
            stats_message += (
                f"📝 Привычка: {habit.name}\n"
                f"🔁 Стрик дней: {habit.current_streak}\n"
                f"📅 Всего выполнено: {habit.total_completed} дней\n\n"
            )

        await message.answer(stats_message)



"""
Блок отметок о выполнении.
"""


@router.message(lambda message: message.text == "📅 Трекинг выполнения")
async def handle_habit_choice(message: Message, state: FSMContext):

    await message.delete()
    await state.set_state(HabitStates.execution)

    await bot.send_message(
        chat_id=message.chat.id,
        text="Выберите действие:",
        reply_markup=completion_marks_keyboard()
    )


@router.callback_query(F.data == "completed", StateFilter(HabitStates.execution))
async def handle_completed_habit(callback: CallbackQuery, state: FSMContext):
    habits = await User.get_unlogged_habits()
    await state.set_state(HabitStates.execution_habit)
    if habits:
        keyb = create_habits_inline_keyboard(habits)
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="Выберите выполненную привычку:",
            reply_markup=keyb
        )
    else:

        await User.authenticate_user(callback.from_user.username, callback.message.chat.id)
        habits = await User.get_unlogged_habits()
        keyb = create_habits_inline_keyboard(habits)
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="Выберите выполненную привычку:",
            reply_markup=keyb
        )


@router.callback_query(F.data == "not_fulfill", StateFilter(HabitStates.execution))
async def handle_completed_habit(callback: CallbackQuery, state: FSMContext):
    habits = await User.get_unlogged_habits()
    await state.set_state(HabitStates.not_completed)
    if habits:
        keyb = create_habits_inline_keyboard(habits)
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="Выберите не выполненную привычку:",
            reply_markup=keyb
        )
    else:

        await User.authenticate_user(callback.from_user.username, callback.message.chat.id)
        habits = await User.get_unlogged_habits()
        keyb = create_habits_inline_keyboard(habits)
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="Выберите не выполненную привычку:",
            reply_markup=keyb
        )


@router.callback_query(F.data.startswith("habit_"), StateFilter(HabitStates.execution_habit, HabitStates.not_completed))
async def handle_delete_habit(callback: CallbackQuery, state: FSMContext):

    habit_id = int(callback.data.split("_")[-1])

    if state == HabitStates.execution_habit:
        log_data = {'completed': True}
    elif state == HabitStates.not_completed:
        log_data = {'completed': False}
    else:
        await callback.message.answer(
            "❌ Ошибка: Неизвестное состояние. Пожалуйста, попробуйте снова.",
            reply_markup=None
        )
        return

    result = await User.create_habit_log(habit_id, log_data)

    if result:

        await callback.message.answer(
            "✅ Вы успешно отметили выполнение привычки!",
            reply_markup=None
        )

        await callback.message.delete()

        await state.clear()
    else:

        await User.authenticate_user(callback.from_user.username, callback.message.chat.id)
        result = await User.create_habit_log(habit_id, log_data)

        if result:

            await callback.message.answer(
                "✅ Вы успешно отметили выполнение привычки!",
                reply_markup=None
            )
            # Удаляем сообщение с клавиатурой
            await callback.message.delete()

            await state.clear()
        else:
            # Если после всех попыток запрос не удался, информируем пользователя об ошибке
            await callback.message.answer(
                "❌ Не удалось отметить выполнение привычки. Пожалуйста, попробуйте снова позже.",
                reply_markup=None
            )


@router.callback_query(F.data == "back",
                       StateFilter(HabitStates.execution_habit, HabitStates.not_completed
                                   )
                       )
async def handle_back(callback: CallbackQuery, state: FSMContext):
    await state.set_state(HabitStates.execution)
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="Выберите действие:",
        reply_markup=completion_marks_keyboard()
    )

"""
Блок самостоятельного создания привычки.
"""


@router.callback_query(F.data == "option", StateFilter(HabitStates.health_menu, HabitStates.useful_habit_menu,
                       HabitStates.sport_menu, HabitStates.nutrition_menu, HabitStates.harmful_habit_menu))
async def handle_useful_habit(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    # Отправляем сообщение с запросом ввода названия привычки и ForceReply
    success_msg = await bot.send_message(
        chat_id=callback.message.chat.id,
        text="Введите название привычки: Например 'Бег'",
        reply_markup=ForceReply()
    )
    if user_id in user_messages:
        user_messages[user_id].append(success_msg.message_id)

    else:
        user_messages[user_id] = [success_msg.message_id]
    # Устанавливаем состояние ожидания ввода названия привычки
    await state.set_state(HabitStates.waiting_for_habit_name)


@router.message(StateFilter(HabitStates.waiting_for_habit_name))
async def process_description(message: Message, state: FSMContext):
    await state.update_data(habit_name=message.text)
    user_id = message.from_user.id

    # Отправляем сообщение с запросом ввода названия привычки и ForceReply
    success_msg = await bot.send_message(
        chat_id=message.chat.id,
        text="Введите описание привычки: Например 'Бегать по утрам'",
        reply_markup=ForceReply()
    )
    if user_id in user_messages:
        user_messages[user_id].append(success_msg.message_id)
        user_messages[user_id].append(message.message_id)
    else:
        user_messages[user_id] = [success_msg.message_id]
    # Устанавливаем состояние ожидания ввода количества дней
    await state.set_state(HabitStates.waiting_for_description)


@router.message(StateFilter(HabitStates.waiting_for_description))
async def process_habit_name(message: Message, state: FSMContext):
    # Сохраняем введенное название привычки в состояние
    await state.update_data(description=message.text)
    user_id = message.from_user.id
    # Запрашиваем у пользователя количество дней отслеживания привычки
    success_msg = await bot.send_message(
        chat_id=message.chat.id,
        text="Сколько дней отслеживаем привычку? (по умолчанию 21 день)",

    )
    if user_id in user_messages:
        user_messages[user_id].append(success_msg.message_id)
        user_messages[user_id].append(message.message_id)
    else:
        user_messages[user_id] = [success_msg.message_id]
    # Устанавливаем состояние ожидания ввода количества дней
    await state.set_state(HabitStates.waiting_for_days)


@router.message(StateFilter(HabitStates.waiting_for_days))
async def process_habit_days(message: Message, state: FSMContext):
    try:
        # Преобразуем сообщение в число дней
        days = int(message.text)
    except ValueError:
        days = 21  # Используем значение по умолчанию

    # Получаем данные из состояния
    user_data = await state.get_data()
    habit_name = user_data.get('habit_name')
    description = user_data.get('description', "")

    # Формируем данные для создания привычки
    habit_data = {
        "name": habit_name,
        "description": description,
        "target_days": days,
        "streak_days": 0,
        "start_date": "2024-09-17",  # Заменить на текущую дату при необходимости
        "last_streak_start": "2024-09-17",
        "current_streak": 0,
        "total_completed": 0
    }

    user_id = message.from_user.id
    # Пытаемся создать привычку через API
    result = await User.create_habit(habit_data)
    if result:
        # Удаляем все предыдущие сообщения пользователя
        if user_id in user_messages:
            for msg_id in user_messages[user_id]:
                await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)

            # Очищаем список сообщений пользователя
            del user_messages[user_id]

        # Отправляем сообщение об успешном создании привычки
        success_msg = await bot.send_message(
            chat_id=message.chat.id,
            text=f"Привычка '{habit_name}' будет отслеживаться {days} дней.",
            reply_markup=get_main_menu_keyboard()
        )

        # Сохраняем ID сообщения в список
        if user_id in user_messages:
            user_messages[user_id].append(success_msg.message_id)
            user_messages[user_id].append(message.message_id)
        else:
            user_messages[user_id] = [success_msg.message_id]
    else:
        # Обновляем токен и повторяем запрос
        await User.authenticate_user(message.from_user.username, message.chat.id)
        result = await User.create_habit(habit_data)
        if result:
            # Удаляем все предыдущие сообщения пользователя
            if user_id in user_messages:
                for msg_id in user_messages[user_id]:
                    await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)

                # Очищаем список сообщений пользователя
                del user_messages[user_id]

            # Отправляем сообщение об успешном создании привычки
            success_msg = await bot.send_message(
                chat_id=message.chat.id,
                text=f"Привычка '{habit_name}' будет отслеживаться {days} дней.",
                reply_markup=get_main_menu_keyboard()
            )

            # Сохраняем ID сообщения в список
            if user_id in user_messages:
                user_messages[user_id].append(success_msg.message_id)
                user_messages[user_id].append(message.message_id)
            else:
                user_messages[user_id] = [success_msg.message_id]
        else:
            await bot.send_message(message.chat.id, f"Неизвестная ошибка")

    # Очищаем состояние
    await state.set_state(HabitStates.main_menu)

"""
Блок  обновления и удаления привычек.
"""


@router.callback_query(F.data == "delete", StateFilter(HabitStates.update_habits_menu))
async def handle_update_habits(callback: CallbackQuery, state: FSMContext):
    habits = await User.get_habits()
    if habits:

        await switch_keyboard(callback, state, HabitStates.habits_menu, lambda: create_habits_inline_keyboard(habits))
    else:
        # Если токен неактуален, обновляем его
        await User.authenticate_user(callback.from_user.username, callback.message.chat.id)
        habits = await User.get_habits()

        await switch_keyboard(callback, state, HabitStates.habits_menu, lambda: create_habits_inline_keyboard(habits))


@router.callback_query(F.data == "change", StateFilter(HabitStates.update_habits_menu))
async def handle_update_habits(callback: CallbackQuery, state: FSMContext):
    habits = await User.get_habits()
    if habits:

        await switch_keyboard(callback, state, HabitStates.habits_change_menu, lambda: create_habits_inline_keyboard(habits))
    else:
        # Если токен неактуален, обновляем его
        await User.authenticate_user(callback.from_user.username, callback.message.chat.id)
        habits = await User.get_habits()

        await switch_keyboard(callback, state, HabitStates.habits_change_menu, lambda: create_habits_inline_keyboard(habits))


@router.callback_query(F.data.startswith("habit_"), StateFilter(HabitStates.habits_menu))
async def handle_delete_habit(callback: CallbackQuery, state: FSMContext):
    habit_id = int(callback.data.split("_")[-1]) # Извлекаем ID привычки из callback_data
    # Здесь добавьте логику для удаления привычки
    result = await User.delete_habit(habit_id)  # Пример вызова метода удаления

    if result:

        # Обновляем клавиатуру после удаления привычки
        habits = await User.get_habits()
        await switch_keyboard(callback, state, HabitStates.habits_menu, lambda: create_habits_inline_keyboard(habits))
    else:

        # Если токен неактуален, обновляем его
        await User.authenticate_user(callback.from_user.username, callback.message.chat.id)
        habits = await User.get_habits()
        await switch_keyboard(callback, state, HabitStates.habits_menu, lambda: create_habits_inline_keyboard(habits))


@router.callback_query(F.data.startswith("habit_"), StateFilter(HabitStates.habits_change_menu))
async def handle_change_habit(callback: CallbackQuery, state: FSMContext):
    habit_id = int(callback.data.split("_")[-1])  # Извлекаем ID привычки из callback_data
    await switch_keyboard(callback, state, HabitStates.habits_change,
                          lambda: create_change_fields_keyboard(habit_id))


@router.callback_query(F.data.startswith("change_"), StateFilter(HabitStates.habits_change))
async def handle_change_field(callback: CallbackQuery, state: FSMContext):
    action, habit_id = callback.data.split("_")[1:3]
    habit_id = int(habit_id)

    if action == "name":
        await callback.message.answer("Введите новое название привычки:")
        await state.update_data(habit_id=habit_id, change_field="name")
        await state.set_state(HabitStates.change_field)
    elif action == "description":
        await callback.message.answer("Введите новое описание привычки:")
        await state.update_data(habit_id=habit_id, change_field="description")
        await state.set_state(HabitStates.change_field)
    elif action == "target_days":
        await callback.message.answer("Введите новые целевые дни:")
        await state.update_data(habit_id=habit_id, change_field="target_days")
        await state.set_state(HabitStates.change_field)
    elif action == "start_date":
        await callback.message.answer("Введите новую дату начала в формате ГГГГ-ММ-ДД:")
        await state.update_data(habit_id=habit_id, change_field="start_date")
        await state.set_state(HabitStates.change_field)


@router.message(StateFilter(HabitStates.change_field))
async def handle_new_value(message: Message, state: FSMContext):
    user_data = await state.get_data()
    habit_id = user_data["habit_id"]
    field_to_change = user_data["change_field"]
    new_value = message.text

    # Подготавливаем данные для обновления привычки
    update_data = {field_to_change: new_value}

    # Логика обновления привычки в базе данных
    response = await User.update_habit(habit_id, update_data)

    if response:
        await message.answer(f"Поле {field_to_change} успешно обновлено!")
    else:
        await User.authenticate_user(message.from_user.username, message.chat.id)
        response = await User.update_habit(habit_id, update_data)
        if response:
            await message.answer(f"Поле {field_to_change} успешно обновлено!")


"""
Блок различных меню и возврат из них.
"""


@router.callback_query(F.data == "track", StateFilter(HabitStates.main_menu))
async def handle_track_habits(callback: CallbackQuery, state: FSMContext):
    await switch_keyboard(callback, state, HabitStates.track_habit_menu, track_habit_keyboard)


@router.callback_query(F.data == "begin", StateFilter(HabitStates.track_habit_menu))
async def handle_begin_track_habits(callback: CallbackQuery, state: FSMContext):
    habits = await User.get_habits()
    if habits:
        await switch_keyboard(callback, state, HabitStates.begin_track_habit,
                              lambda: create_track_habits_inline_keyboard(habits, False))
    else:
        await User.authenticate_user(callback.from_user.username, callback.message.chat.id)
        habits = await User.get_habits()
        await switch_keyboard(callback, state, HabitStates.begin_track_habit,
                              lambda: create_track_habits_inline_keyboard(habits, False))


@router.callback_query(F.data == "cease", StateFilter(HabitStates.track_habit_menu))
async def handle_cease_track_habits(callback: CallbackQuery, state: FSMContext):
    habits = await User.get_habits()
    if habits:
        await switch_keyboard(callback, state, HabitStates.cease_track_habit,
                              lambda: create_track_habits_inline_keyboard(habits, True))
    else:
        await User.authenticate_user(callback.from_user.username, callback.message.chat.id)
        habits = await User.get_habits()
        await switch_keyboard(callback, state, HabitStates.cease_track_habit,
                              lambda: create_track_habits_inline_keyboard(habits, True))


@router.callback_query(F.data.startswith("habit_"), StateFilter(HabitStates.begin_track_habit,
                                                                HabitStates.cease_track_habit))
async def handle_back(callback: CallbackQuery, state: FSMContext):
    # Получаем текущее состояние
    current_state = await state.get_state()
    match  current_state:
        case HabitStates.begin_track_habit.state:
            habit_id = int(callback.data.split("_")[-1])  # Извлекаем ID привычки из callback_data
            # Подготавливаем данные для обновления привычки
            update_data = {"is_tracked": True}
            # Логика обновления привычки в базе данных
            response = await User.update_habit(habit_id, update_data)
            if response:
                await switch_keyboard(callback, state, HabitStates.main_menu, get_habit_choice_keyboard)
            else:
                await User.authenticate_user(callback.from_user.username, callback.message.chat.id)
                response = await User.update_habit(habit_id, update_data)
                await switch_keyboard(callback, state, HabitStates.main_menu, get_habit_choice_keyboard)

        case HabitStates.cease_track_habit.state:
            habit_id = int(callback.data.split("_")[-1])  # Извлекаем ID привычки из callback_data
            # Подготавливаем данные для обновления привычки
            update_data = {"is_tracked": False}
            # Логика обновления привычки в базе данных
            response = await User.update_habit(habit_id, update_data)
            if response:
                await switch_keyboard(callback, state, HabitStates.main_menu, get_habit_choice_keyboard)
            else:
                await User.authenticate_user(callback.from_user.username, callback.message.chat.id)
                response = await User.update_habit(habit_id, update_data)
                await switch_keyboard(callback, state, HabitStates.main_menu, get_habit_choice_keyboard)


@router.callback_query(F.data == "update_habits", StateFilter(HabitStates.main_menu))
async def handle_update_habits(callback: CallbackQuery, state: FSMContext):
    await switch_keyboard(callback, state, HabitStates.update_habits_menu, update_habits_keyboard)


@router.callback_query(F.data == "harmful", StateFilter(HabitStates.main_menu))
async def handle_harmful_habit(callback: CallbackQuery, state: FSMContext):
    await switch_keyboard(callback, state, HabitStates.harmful_habit_menu, harmful_habit_choice_keyboard)


@router.callback_query(F.data == "useful", StateFilter(HabitStates.main_menu))
async def handle_useful_habit(callback: CallbackQuery, state: FSMContext):
    await switch_keyboard(callback, state, HabitStates.useful_habit_menu, useful_habit_choice_keyboard)


@router.callback_query(F.data == "health", StateFilter(HabitStates.useful_habit_menu))
async def handle_health(callback: CallbackQuery, state: FSMContext):
    await switch_keyboard(callback, state, HabitStates.health_menu, health_habit_keyboard)


@router.callback_query(F.data == "sport", StateFilter(HabitStates.useful_habit_menu))
async def handle_health(callback: CallbackQuery, state: FSMContext):
    await switch_keyboard(callback, state, HabitStates.sport_menu, sport_habit_keyboard)


@router.callback_query(F.data == "nutrition", StateFilter(HabitStates.useful_habit_menu))
async def handle_health(callback: CallbackQuery, state: FSMContext):
    await switch_keyboard(callback, state, HabitStates.nutrition_menu, nutrition_habit_keyboard)


@router.callback_query(F.data == "back",
                       StateFilter(HabitStates.health_menu, HabitStates.useful_habit_menu, HabitStates.sport_menu,
                                   HabitStates.nutrition_menu, HabitStates.harmful_habit_menu,
                                   HabitStates.update_habits_menu, HabitStates.habits_menu, HabitStates.habits_change,
                                   HabitStates.habits_change_menu, HabitStates.track_habit_menu,
                                   HabitStates.begin_track_habit, HabitStates.cease_track_habit,
                                   )
                       )
async def handle_back(callback: CallbackQuery, state: FSMContext):
    # Получаем текущее состояние
    current_state = await state.get_state()
    match  current_state:
        case HabitStates.health_menu.state:
            #Возвращаемся в меню полезных привычек
            await switch_keyboard(callback, state, HabitStates.useful_habit_menu, useful_habit_choice_keyboard)
        case HabitStates.sport_menu.state:
            # Возвращаемся в меню полезных привычек
            await switch_keyboard(callback, state, HabitStates.useful_habit_menu, useful_habit_choice_keyboard)
        case HabitStates.nutrition_menu.state:
            # Возвращаемся в меню полезных привычек
            await switch_keyboard(callback, state, HabitStates.useful_habit_menu, useful_habit_choice_keyboard)
        case HabitStates.useful_habit_menu.state:
            # Возвращаемся в главное меню
            await switch_keyboard(callback, state, HabitStates.main_menu, get_habit_choice_keyboard)
        case HabitStates.harmful_habit_menu.state:
            # Возвращаемся в главное меню
            await switch_keyboard(callback, state, HabitStates.main_menu, get_habit_choice_keyboard)
        case HabitStates.update_habits_menu.state:
            # Возвращаемся в главное меню
            await switch_keyboard(callback, state, HabitStates.main_menu, get_habit_choice_keyboard)
        case HabitStates.habits_menu.state:
            # Возвращаемся в главное меню
            await switch_keyboard(callback, state, HabitStates.main_menu, get_habit_choice_keyboard)
        case HabitStates.habits_change.state:
            # Возвращаемся в главное меню
            await switch_keyboard(callback, state, HabitStates.main_menu, get_habit_choice_keyboard)
        case HabitStates.habits_change_menu.state:
            # Возвращаемся в главное меню
            await switch_keyboard(callback, state, HabitStates.main_menu, get_habit_choice_keyboard)
        case HabitStates.track_habit_menu.state:
            # Возвращаемся в главное меню
            await switch_keyboard(callback, state, HabitStates.main_menu, get_habit_choice_keyboard)
        case HabitStates.begin_track_habit.state:
            # Возвращаемся в главное меню
            await switch_keyboard(callback, state, HabitStates.track_habit_menu, track_habit_keyboard)


"""
Блок обработки дефолтных значений.
"""
default_habits = {
    "sleep": {"name": "Сон", "description": "Здоровый сон", "target_days": 30},
    "hydration": {"name": "Гидратация", "description": "Пить больше воды", "target_days": 21},
    "meditation": {"name": "Медитация", "description": "Медитация каждый день", "target_days": 21},
    "strength_training": {"name": "Силовые тренировки", "description": "Тренировки для силы", "target_days": 30},
    "running": {"name": "Бег", "description": "Бег по утрам", "target_days": 21},
    "swimming": {"name": "Плавание", "description": "Ежедневное плавание", "target_days": 30},
    "fruits_veggies": {"name": "Фрукты и овощи", "description": "Употребление фруктов и овощей", "target_days": 21},
    "breakfast": {"name": "Завтрак", "description": "Здоровый завтрак каждый день", "target_days": 21},
    "less_sugar": {"name": "Меньше сахара", "description": "Снизить потребление сахара", "target_days": 21},
    "smoking": {"name": "Отказ от курения", "description": "Бросить курить", "target_days": 30},
    "alcohol": {"name": "Отказ от алкоголя", "description": "Не употреблять алкоголь", "target_days": 30},
}


@router.callback_query(F.data.in_(default_habits.keys()),
                       StateFilter(HabitStates.health_menu, HabitStates.useful_habit_menu,
                                   HabitStates.sport_menu, HabitStates.nutrition_menu, HabitStates.harmful_habit_menu))
async def handle_useful_habit(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    habit_key = callback.data  # Извлекаем ключ привычки, соответствующий нажатию

    # Получаем дефолтные значения привычки
    habit_data = default_habits.get(habit_key, None)

    if habit_data:
        # Формируем данные для создания привычки
        new_habit = {
            "name": habit_data["name"],
            "description": habit_data["description"],
            "target_days": habit_data["target_days"],
            "streak_days": 0,
            "start_date": "2024-09-17",  # Можно использовать текущую дату
            "last_streak_start": "2024-09-17",
            "current_streak": 0,
            "total_completed": 0
        }
        # Попытка создать привычку через метод User.create_habit
        result = await User.create_habit(new_habit)

        if result:
            # Уведомляем пользователя об успешном создании привычки
            success_msg = await bot.send_message(
                chat_id=callback.message.chat.id,
                text=f"Привычка '{new_habit['name']}' создана и будет отслеживаться {new_habit['target_days']} дней.",
                reply_markup=get_main_menu_keyboard()  # Вернуть основное меню
            )
            if user_id in user_messages:
                del user_messages[user_id]
            # Сохраняем ID сообщения в список для последующего удаления
            if user_id in user_messages:
                user_messages[user_id].append(success_msg.message_id)
                user_messages[user_id].append(callback.message_id)
            else:
                user_messages[user_id] = [success_msg.message_id]
        else:
            # Если токен неактуален, обновляем его
            await User.authenticate_user(callback.from_user.username, callback.message.chat.id)
            # Повторяем попытку создать привычку после обновления токена
            result = await User.create_habit(new_habit)
            if result:
                # Уведомляем пользователя об успешном создании привычки
                success_msg = await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f"Привычка '{new_habit['name']}' создана и будет отслеживаться {new_habit['target_days']} дней.",
                    reply_markup=get_main_menu_keyboard()  # Вернуть основное меню
                )
                if user_id in user_messages:
                    del user_messages[user_id]
                # Сохраняем ID сообщения в список для последующего удаления
                if user_id in user_messages:
                    user_messages[user_id].append(success_msg.message_id)
                    user_messages[user_id].append(callback.message_id)
                else:
                    user_messages[user_id] = [success_msg.message_id]
            else:
                # Обработка неуспешного ответа от API
                detail = result.get('detail', 'Неизвестная ошибка') if isinstance(result,
                                                                                  dict) else "Неверный формат ответа от сервера."
                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f"Не удалось создать привычку: {detail}."
                )

