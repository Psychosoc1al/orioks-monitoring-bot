import asyncio
import logging
import os
import pickle
import random
from datetime import datetime

import aiohttp
import aioschedule

import db.notify_settings
import db.user_status
from app.exceptions import OrioksParseDataException
from app.helpers import CommonHelper, TelegramMessageHelper
from checking.marks.get_orioks_marks import user_marks_check
from checking.news.get_orioks_news import get_current_new, user_news_check_from_news_id
from checking.homeworks.get_orioks_homeworks import user_homeworks_check
from checking.requests.get_orioks_requests import user_requests_check
from http.cookies import SimpleCookie
from config import Config


def _get_user_orioks_cookies_from_telegram_id(user_telegram_id: int) -> SimpleCookie:
    path_to_cookies = os.path.join(Config.BASEDIR, 'users_data', 'cookies', f'{user_telegram_id}.pkl')
    return SimpleCookie(pickle.load(open(path_to_cookies, 'rb')))


def _delete_users_tracking_data_in_notify_settings_off(user_telegram_id: int, user_notify_settings: dict) -> None:
    if not user_notify_settings['marks']:
        CommonHelper.safe_delete(
            os.path.join(Config.PATH_TO_STUDENTS_TRACKING_DATA, 'marks', f'{user_telegram_id}.json')
        )
    if not user_notify_settings['news']:
        CommonHelper.safe_delete(
            os.path.join(Config.PATH_TO_STUDENTS_TRACKING_DATA, 'news', f'{user_telegram_id}.json')
        )
    if not user_notify_settings['discipline_sources']:
        CommonHelper.safe_delete(os.path.join(
            Config.PATH_TO_STUDENTS_TRACKING_DATA, 'discipline_sources', f'{user_telegram_id}.json')
        )
    if not user_notify_settings['homeworks']:
        CommonHelper.safe_delete(os.path.join(
            Config.PATH_TO_STUDENTS_TRACKING_DATA, 'homeworks', f'{user_telegram_id}.json')
        )
    if not user_notify_settings['requests']:
        CommonHelper.safe_delete(os.path.join(
            Config.PATH_TO_STUDENTS_TRACKING_DATA, 'requests', f'{user_telegram_id}.json')
        )


async def make_one_user_check(user_telegram_id: int) -> None:
    user_notify_settings = db.notify_settings.get_user_notify_settings_to_dict(user_telegram_id=user_telegram_id)
    cookies = _get_user_orioks_cookies_from_telegram_id(user_telegram_id=user_telegram_id)
    async with aiohttp.ClientSession(
            cookies=cookies,
            timeout=Config.REQUESTS_TIMEOUT,
            headers=Config.ORIOKS_REQUESTS_HEADERS
    ) as session:
        if user_notify_settings['marks']:
            await user_marks_check(user_telegram_id=user_telegram_id, session=session)
        if user_notify_settings['discipline_sources']:
            pass  # TODO: user_discipline_sources_check(user_telegram_id=user_telegram_id, session=session)
        if user_notify_settings['homeworks']:
            await user_homeworks_check(user_telegram_id=user_telegram_id, session=session)
        if user_notify_settings['requests']:
            await user_requests_check(user_telegram_id=user_telegram_id, session=session)
    _delete_users_tracking_data_in_notify_settings_off(
        user_telegram_id=user_telegram_id,
        user_notify_settings=user_notify_settings
    )


async def make_all_users_news_check(tries_counter: int = 0) -> list:
    tasks = []
    users_to_check_news = db.notify_settings.select_all_news_enabled_users()
    if len(users_to_check_news) == 0:
        return []
    picked_user_to_check_news = random.choice(list(users_to_check_news))
    if tries_counter > 10:
        return []
    cookies = _get_user_orioks_cookies_from_telegram_id(user_telegram_id=picked_user_to_check_news)
    try:
        async with aiohttp.ClientSession(
                cookies=cookies,
                timeout=Config.REQUESTS_TIMEOUT,
                headers=Config.ORIOKS_REQUESTS_HEADERS
        ) as session:
            current_new = await get_current_new(user_telegram_id=picked_user_to_check_news, session=session)
    except OrioksParseDataException:
        return await make_all_users_news_check(tries_counter=tries_counter + 1)
    for user_telegram_id in users_to_check_news:
        try:
            cookies = _get_user_orioks_cookies_from_telegram_id(user_telegram_id=user_telegram_id)
        except FileNotFoundError:
            logging.error('(COOKIES) FileNotFoundError: %s' % (user_telegram_id, ))
            continue
        user_session = aiohttp.ClientSession(cookies=cookies, timeout=Config.REQUESTS_TIMEOUT)
        tasks.append(user_news_check_from_news_id(
            user_telegram_id=user_telegram_id,
            session=user_session,
            current_new=current_new
        ))
    return tasks


async def run_requests(tasks: list) -> None:
    try:
        await asyncio.gather(*tasks)
    except asyncio.TimeoutError:
        await TelegramMessageHelper.message_to_admins(message='Сервер ОРИОКС не отвечает')
        return
    except Exception as e:
        logging.error('Ошибка в запросах ОРИОКС!\n %s' % (e, ))
        await TelegramMessageHelper.message_to_admins(message=f'Ошибка в запросах ОРИОКС!\n{e}')


async def do_checks():
    logging.info('started: %s' % (datetime.now().strftime("%H:%M:%S %d.%m.%Y"),))
    users_to_check = db.user_status.select_all_orioks_authenticated_users()

    tasks = [] + await make_all_users_news_check()
    for user_telegram_id in users_to_check:
        tasks.append(make_one_user_check(
            user_telegram_id=user_telegram_id
        ))
    await run_requests(tasks=tasks)
    logging.info('ended: %s' % (datetime.now().strftime("%H:%M:%S %d.%m.%Y"),))


async def scheduler():
    await TelegramMessageHelper.message_to_admins(message='Бот запущен!')
    aioschedule.every(Config.ORIOKS_SECONDS_BETWEEN_WAVES).seconds.do(do_checks)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())
