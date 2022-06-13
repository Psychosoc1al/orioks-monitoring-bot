from aiogram import types
from aiogram.utils import markdown

from app.handlers import AbstractCommandHandler


class FAQCommandHandler(AbstractCommandHandler):

    @staticmethod
    async def process(message: types.Message, *args, **kwargs):
        await message.reply(
            markdown.text(
                markdown.text('https://orioks-monitoring.github.io/bot/faq'),
            ),
            disable_web_page_preview=True,
        )
