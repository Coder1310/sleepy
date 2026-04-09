from __future__ import annotations

from datetime import date
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SleepEntry


async def add_sleep_entry(
  session: AsyncSession,
  *,
  user_id: int,
  mode: str,
  duration_minutes: int,
  quality: int,
  felt_after: int,
  stress_before: int,
  sleepiness_before: int,
  notes: str | None = None,
) -> SleepEntry:
  entry = SleepEntry(
    user_id=user_id,
    entry_date=date.today(),
    mode=mode,
    duration_minutes=duration_minutes,
    subjective_sleep_quality_1_5=quality,
    felt_after_waking_1_5=felt_after,
    stress_before_sleep_1_5=stress_before,
    sleepiness_before_sleep_1_5=sleepiness_before,
    notes=notes,
  )
  session.add(entry)
  await session.commit()
  await session.refresh(entry)
  return entry


async def get_recent_entries(
  session: AsyncSession,
  *,
  user_id: int,
  limit: int = 7,
) -> list[SleepEntry]:
  result = await session.execute(
    select(SleepEntry)
    .where(SleepEntry.user_id == user_id)
    .order_by(desc(SleepEntry.created_at))
    .limit(limit)
  )
  return list(result.scalars().all())
