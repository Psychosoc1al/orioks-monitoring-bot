import os
import db.user_status
import db.notify_settings
from config import Config
from utils.delete_file import safe_delete


def make_orioks_logout(user_telegram_id: int) -> None:
    safe_delete(os.path.join(Config.BASEDIR, 'users_data', 'cookies', f'{user_telegram_id}.pkl'))

    safe_delete(os.path.join(Config.PATH_TO_STUDENTS_TRACKING_DATA, 'discipline_sources', f'{user_telegram_id}.json'))

    safe_delete(os.path.join(Config.PATH_TO_STUDENTS_TRACKING_DATA, 'news', f'{user_telegram_id}.json'))

    safe_delete(os.path.join(Config.PATH_TO_STUDENTS_TRACKING_DATA, 'marks', f'{user_telegram_id}.json'))

    safe_delete(os.path.join(Config.PATH_TO_STUDENTS_TRACKING_DATA, 'homeworks', f'{user_telegram_id}.json'))

    safe_delete(os.path.join(Config.PATH_TO_STUDENTS_TRACKING_DATA, 'requests', 'questionnaire',
                             f'{user_telegram_id}.json'))
    safe_delete(os.path.join(Config.PATH_TO_STUDENTS_TRACKING_DATA, 'requests', 'doc', f'{user_telegram_id}.json'))
    safe_delete(os.path.join(Config.PATH_TO_STUDENTS_TRACKING_DATA, 'requests', 'reference',
                             f'{user_telegram_id}.json'))

    db.user_status.update_user_orioks_authenticated_status(
        user_telegram_id=user_telegram_id,
        is_user_orioks_authenticated=False
    )
    db.notify_settings.update_user_notify_settings_reset_to_default(user_telegram_id=user_telegram_id)
