from __future__ import annotations

import json

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FeedbackEntry, SessionRequest
from app.schemas import Recommendation


async def create_session_request(
  session: AsyncSession,
  *,
  user_id: int,
  requested_mode: str,
  free_time_minutes: int,
  slept_last_night_minutes: int,
  current_energy_1_5: int,
  current_sleepiness_1_5: int,
  current_stress_1_5: int,
  wants_alarm: bool,
  recommendation: Recommendation,
) -> SessionRequest:
  item = SessionRequest(
    user_id=user_id,
    requested_mode=requested_mode,
    free_time_minutes=free_time_minutes,
    slept_last_night_minutes=slept_last_night_minutes,
    current_energy_1_5=current_energy_1_5,
    current_sleepiness_1_5=current_sleepiness_1_5,
    current_stress_1_5=current_stress_1_5,
    wants_alarm=wants_alarm,
    recommended_plan_json=recommendation.model_dump_json(ensure_ascii=False),
  )
  session.add(item)
  await session.commit()
  await session.refresh(item)
  return item


async def get_last_session_request(session: AsyncSession, *, user_id: int) -> SessionRequest | None:
  result = await session.execute(
    select(SessionRequest)
    .where(SessionRequest.user_id == user_id)
    .order_by(desc(SessionRequest.requested_at))
    .limit(1)
  )
  return result.scalar_one_or_none()


async def add_feedback(
  session: AsyncSession,
  *,
  user_id: int,
  session_request_id: int | None,
  was_helpful_1_5: int,
  user_followed_plan: bool,
  comments: str | None = None,
) -> FeedbackEntry:
  item = FeedbackEntry(
    user_id=user_id,
    session_request_id=session_request_id,
    was_helpful_1_5=was_helpful_1_5,
    user_followed_plan=user_followed_plan,
    comments=comments,
  )
  session.add(item)
  await session.commit()
  await session.refresh(item)
  return item
