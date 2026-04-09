from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User


async def get_or_create_user(session: AsyncSession, telegram_id: int, name: str | None) -> User:
  result = await session.execute(select(User).where(User.telegram_id == telegram_id))
  user = result.scalar_one_or_none()
  if user is not None:
    if name and user.name != name:
      user.name = name
      await session.commit()
    return user

  user = User(
    telegram_id=telegram_id,
    name=name,
    timezone=settings.default_timezone,
  )
  session.add(user)
  await session.commit()
  await session.refresh(user)
  return user
