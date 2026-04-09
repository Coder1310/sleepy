import asyncio
import logging

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.db import async_session_factory, engine
from app.models import Base
from app.scheduler import scheduler
from app.services.alarm_service import restore_active_alarms
from bot.handlers import router


class DbSessionMiddleware(BaseMiddleware):
  def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
    self.session_factory = session_factory

  async def __call__(self, handler, event: TelegramObject, data: dict):
    async with self.session_factory() as session:
      data["session"] = session
      data["session_factory"] = self.session_factory
      return await handler(event, data)


async def init_db() -> None:
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
  logging.basicConfig(level=logging.INFO)
  await init_db()

  bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
  )
  dp = Dispatcher()
  dp.update.middleware(DbSessionMiddleware(async_session_factory))
  dp.include_router(router)

  scheduler.start()
  await restore_active_alarms(bot=bot, session_factory=async_session_factory)

  try:
    await dp.start_polling(bot)
  finally:
    scheduler.shutdown(wait=False)
    await bot.session.close()


if __name__ == "__main__":
  asyncio.run(main())
