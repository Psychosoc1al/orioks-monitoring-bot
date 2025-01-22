import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from sqlalchemy.orm.scoping import ScopedSession

from config import config


def initialize_database() -> ScopedSession:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker

    engine = create_engine(config.DATABASE_URL, convert_unicode=True)
    return scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )


def initialize_assets():
    from app.helpers.AssetsHelper import assets_helper

    current_folder_path = os.path.dirname(os.path.abspath(__file__))
    assets_helper.initialize(f'{current_folder_path}/assets')


def _settings_before_start() -> None:
    from app.fixtures import initialize_default_values
    from app.handlers import register_handlers
    from app.helpers import CommonHelper
    from app.middlewares import (
        AdminCommandsMiddleware,
        UserAgreementMiddleware,
        UserOrioksAttemptsMiddleware,
    )

    register_handlers(dispatcher=dispatcher)
    initialize_assets()
    initialize_default_values()
    dispatcher.middleware.setup(UserAgreementMiddleware())
    dispatcher.middleware.setup(UserOrioksAttemptsMiddleware())
    dispatcher.middleware.setup(AdminCommandsMiddleware())
    CommonHelper.make_dirs()


bot = Bot(token=config.TELEGRAM_BOT_API_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)

db_session = initialize_database()


def run():
    from checking import on_startup

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s - %(module)s - %(funcName)s - %(lineno)d: %(message)s",
        datefmt='%H:%M:%S %d.%m.%Y',
    )
    _settings_before_start()
    executor.start_polling(
        dispatcher, skip_updates=True, on_startup=on_startup.on_startup
    )
