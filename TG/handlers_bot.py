

from aiogram import F, Router

from aiogram.filters import CommandStart, StateFilter

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from loguru import logger


from TG.StatesGroup import HabitStates, switch_keyboard
from TG.bot import bot
from TG.funcs_tg import User
from TG.keyboards.InlineKeyboard import (get_habit_choice_keyboard, useful_habit_choice_keyboard,
                                         harmful_habit_choice_keyboard, health_habit_keyboard, sport_habit_keyboard,
                                         nutrition_habit_keyboard)
from TG.keyboards.ReplyKeyboard import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message):
    user = message.from_user
    username = user.username
    chat_id = message.chat.id

    # Попытка аутентификации пользователя
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


@router.message(lambda message: message.text == "📅 Выбор привычек")
async def handle_habit_choice(message: Message, state: FSMContext):
    # Удаляем сообщение пользователя
    await message.delete()
    await state.set_state(HabitStates.main_menu)
    # Отправляем новое сообщение с новой клавиатурой
    await bot.send_message(
        chat_id=message.chat.id,
        text="Выберите действие:",
        reply_markup=get_habit_choice_keyboard()
    )


@router.callback_query(F.data == "harmful", StateFilter(HabitStates.main_menu))
async def handle_useful_habit(callback: CallbackQuery, state: FSMContext):
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
                       StateFilter(HabitStates.health_menu, HabitStates.useful_habit_menu,
                                   HabitStates.sport_menu, HabitStates.nutrition_menu, HabitStates.harmful_habit_menu))
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

