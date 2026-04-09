from __future__ import annotations

import random
from datetime import datetime, timedelta

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Alarm, User
from app.scheduler import scheduler


def generate_alarm_code() -> str:
  return f"{random.randint(1000, 9999)}"


def _job_id(alarm_id: int, suffix: str) -> str:
  return f"alarm_{alarm_id}_{suffix}"


async def create_alarm(
  session: AsyncSession,
  *,
  user_id: int,
  alarm_time: datetime,
) -> Alarm:
  alarm = Alarm(
    user_id=user_id,
    alarm_time=alarm_time,
    code=generate_alarm_code(),
    is_active=True,
  )
  session.add(alarm)
  await session.commit()
  await session.refresh(alarm)
  return alarm


def remove_alarm_jobs(alarm_id: int) -> None:
  for suffix in ("start", "r1", "r2"):
    job_id = _job_id(alarm_id, suffix)
    if scheduler.get_job(job_id) is not None:
      scheduler.remove_job(job_id)


async def deactivate_alarm(
  session: AsyncSession,
  *,
  user_id: int,
  code: str,
) -> bool:
  result = await session.execute(
    select(Alarm).where(
      Alarm.user_id == user_id,
      Alarm.code == code,
      Alarm.is_active.is_(True),
    )
  )
  alarm = result.scalar_one_or_none()
  if alarm is None:
    return False

  alarm.is_active = False
  alarm.stop_confirmed_at = datetime.utcnow()
  await session.commit()
  remove_alarm_jobs(alarm.id)
  return True


async def _send_alarm_if_active(
  *,
  bot: Bot,
  session_factory: async_sessionmaker[AsyncSession],
  chat_id: int,
  alarm_id: int,
  code: str,
  is_reminder: bool,
) -> None:
  async with session_factory() as session:
    result = await session.execute(select(Alarm).where(Alarm.id == alarm_id))
    alarm = result.scalar_one_or_none()
    if alarm is None or not alarm.is_active:
      remove_alarm_jobs(alarm_id)
      return

  prefix = "Напоминание будильника" if is_reminder else "Будильник"
  await bot.send_message(
    chat_id,
    (
      f"{prefix}. Чтобы выключить его, отправь код: {code}\n"
      f"Можно также использовать команду /stop_alarm {code}"
    ),
  )


def schedule_alarm_jobs(
  *,
  bot: Bot,
  session_factory: async_sessionmaker[AsyncSession],
  chat_id: int,
  alarm_id: int,
  code: str,
  run_at: datetime,
) -> None:
  start_at = max(run_at, datetime.utcnow() + timedelta(seconds=3))
  remove_alarm_jobs(alarm_id)

  scheduler.add_job(
    _send_alarm_if_active,
    trigger="date",
    run_date=start_at,
    id=_job_id(alarm_id, "start"),
    replace_existing=True,
    kwargs={
      "bot": bot,
      "session_factory": session_factory,
      "chat_id": chat_id,
      "alarm_id": alarm_id,
      "code": code,
      "is_reminder": False,
    },
  )

  for delay_seconds, suffix in ((30, "r1"), (90, "r2")):
    scheduler.add_job(
      _send_alarm_if_active,
      trigger="date",
      run_date=start_at + timedelta(seconds=delay_seconds),
      id=_job_id(alarm_id, suffix),
      replace_existing=True,
      kwargs={
        "bot": bot,
        "session_factory": session_factory,
        "chat_id": chat_id,
        "alarm_id": alarm_id,
        "code": code,
        "is_reminder": True,
      },
    )


async def restore_active_alarms(
  *,
  bot: Bot,
  session_factory: async_sessionmaker[AsyncSession],
) -> None:
  async with session_factory() as session:
    result = await session.execute(
      select(Alarm, User.telegram_id)
      .join(User, User.id == Alarm.user_id)
      .where(Alarm.is_active.is_(True))
    )
    items = list(result.all())

  for alarm, telegram_id in items:
    schedule_alarm_jobs(
      bot=bot,
      session_factory=session_factory,
      chat_id=telegram_id,
      alarm_id=alarm.id,
      code=alarm.code,
      run_at=alarm.alarm_time,
    )
