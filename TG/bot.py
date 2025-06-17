from aiogram import Bot, Dispatcher
from config import config
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode


session = AiohttpSession()
bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML), session=session)

dp = Dispatcher()
