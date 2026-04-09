from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
  pass


class User(Base):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
  name: Mapped[str | None] = mapped_column(String(255), nullable=True)
  timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
  premium_status: Mapped[bool] = mapped_column(Boolean, default=False)
  preferred_language: Mapped[str] = mapped_column(String(16), default="ru")
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

  sleep_entries: Mapped[list["SleepEntry"]] = relationship(back_populates="user")
  session_requests: Mapped[list["SessionRequest"]] = relationship(back_populates="user")
  alarms: Mapped[list["Alarm"]] = relationship(back_populates="user")
  feedback_entries: Mapped[list["FeedbackEntry"]] = relationship(back_populates="user")


class SleepEntry(Base):
  __tablename__ = "sleep_entries"

  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
  entry_date: Mapped[date] = mapped_column(Date)
  mode: Mapped[str] = mapped_column(String(32))
  duration_minutes: Mapped[int] = mapped_column(Integer)
  subjective_sleep_quality_1_5: Mapped[int] = mapped_column(Integer)
  felt_after_waking_1_5: Mapped[int] = mapped_column(Integer)
  stress_before_sleep_1_5: Mapped[int] = mapped_column(Integer)
  sleepiness_before_sleep_1_5: Mapped[int] = mapped_column(Integer)
  notes: Mapped[str | None] = mapped_column(Text, nullable=True)
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

  user: Mapped["User"] = relationship(back_populates="sleep_entries")


class SessionRequest(Base):
  __tablename__ = "session_requests"

  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
  requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  requested_mode: Mapped[str] = mapped_column(String(16))
  free_time_minutes: Mapped[int] = mapped_column(Integer)
  slept_last_night_minutes: Mapped[int] = mapped_column(Integer)
  current_energy_1_5: Mapped[int] = mapped_column(Integer)
  current_sleepiness_1_5: Mapped[int] = mapped_column(Integer)
  current_stress_1_5: Mapped[int] = mapped_column(Integer)
  wants_alarm: Mapped[bool] = mapped_column(Boolean, default=False)
  recommended_plan_json: Mapped[str] = mapped_column(Text)

  user: Mapped["User"] = relationship(back_populates="session_requests")
  feedback_entries: Mapped[list["FeedbackEntry"]] = relationship(back_populates="session_request")


class Alarm(Base):
  __tablename__ = "alarms"

  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
  alarm_time: Mapped[datetime] = mapped_column(DateTime, index=True)
  code: Mapped[str] = mapped_column(String(12), index=True)
  is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
  stop_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

  user: Mapped["User"] = relationship(back_populates="alarms")


class FeedbackEntry(Base):
  __tablename__ = "feedback_entries"

  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
  session_request_id: Mapped[int | None] = mapped_column(ForeignKey("session_requests.id"), nullable=True)
  was_helpful_1_5: Mapped[int] = mapped_column(Integer)
  user_followed_plan: Mapped[bool] = mapped_column(Boolean, default=True)
  comments: Mapped[str | None] = mapped_column(Text, nullable=True)
  created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

  user: Mapped["User"] = relationship(back_populates="feedback_entries")
  session_request: Mapped["SessionRequest | None"] = relationship(back_populates="feedback_entries")
