from __future__ import annotations

from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.recommendation_engine import build_recommendation
from app.services.alarm_service import create_alarm, deactivate_alarm, schedule_alarm_jobs
from app.services.session_service import add_feedback, create_session_request, get_last_session_request
from app.services.sleep_service import add_sleep_entry, get_recent_entries
from app.services.stats_service import build_history_text, build_stats_text
from app.services.user_service import get_or_create_user
from bot.keyboards import main_menu, sleep_mode_keyboard
from bot.states import DayFlow, NightFlow, PowerNapFlow, WakeFlow
from bot.texts import DISCLAIMER, HELP_TEXT, PREMIUM_TEXT, SETTINGS_TEXT, START_TEXT


router = Router()


def _parse_int(text: str) -> int | None:
  try:
    return int(text.strip())
  except (TypeError, ValueError):
    return None


async def _send_main_menu(message: Message, text: str) -> None:
  await message.answer(text, reply_markup=main_menu)


async def _build_plan_message(
  *,
  recommendation,
  alarm_minutes: int,
  message: Message,
  session: AsyncSession,
  session_factory: async_sessionmaker[AsyncSession],
  bot: Bot,
  user_id: int,
) -> str:
  answer_lines = [
    f"Режим: {recommendation.recommended_mode}",
    f"Длительность: {recommendation.recommended_duration_minutes} мин",
    "",
    recommendation.explanation_for_user,
    "",
    "Шаги:",
    *[f"- {step}" for step in recommendation.steps],
    "",
    f"Опциональный звук: {recommendation.optional_audio_type}",
  ]

  if alarm_minutes > 0:
    alarm_time = datetime.utcnow() + timedelta(minutes=alarm_minutes)
    alarm = await create_alarm(session, user_id=user_id, alarm_time=alarm_time)
    schedule_alarm_jobs(
      bot=bot,
      session_factory=session_factory,
      chat_id=message.from_user.id,
      alarm_id=alarm.id,
      code=alarm.code,
      run_at=alarm.alarm_time,
    )
    answer_lines.extend(
      [
        "",
        f"Будильник поставлен на {alarm_minutes} минут.",
        f"Код для выключения: {alarm.code}",
      ]
    )

  answer_lines.extend(["", DISCLAIMER])
  return "\n".join(answer_lines)


@router.message(Command("start"))
async def start_handler(message: Message, session: AsyncSession) -> None:
  await get_or_create_user(session, message.from_user.id, message.from_user.full_name)
  await _send_main_menu(message, START_TEXT)


@router.message(Command("menu"))
@router.message(F.text == "В меню")
async def menu_handler(message: Message, state: FSMContext) -> None:
  await state.clear()
  await _send_main_menu(message, "Главное меню")


@router.message(Command("help"))
@router.message(F.text == "Помощь")
async def help_handler(message: Message) -> None:
  await _send_main_menu(message, HELP_TEXT)


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
  await state.clear()
  await _send_main_menu(message, "Текущий сценарий отменен.")


@router.message(Command("stop_alarm"))
async def stop_alarm_command(
  message: Message,
  command: CommandObject,
  session: AsyncSession,
) -> None:
  code = (command.args or "").strip()
  user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name)
  if not code:
    await message.answer("Используй команду так: /stop_alarm 1234")
    return

  ok = await deactivate_alarm(session, user_id=user.id, code=code)
  if ok:
    await _send_main_menu(message, "Будильник выключен.")
  else:
    await message.answer("Не удалось найти активный будильник с таким кодом.")


@router.message(F.text == "Настройки")
async def settings_handler(message: Message) -> None:
  await _send_main_menu(message, SETTINGS_TEXT)


@router.message(F.text == "Premium")
async def premium_handler(message: Message) -> None:
  await _send_main_menu(message, PREMIUM_TEXT)


@router.message(F.text == "История")
async def history_handler(message: Message, session: AsyncSession) -> None:
  user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name)
  entries = await get_recent_entries(session, user_id=user.id, limit=10)
  await _send_main_menu(message, build_history_text(entries))


@router.message(F.text == "Статистика")
async def stats_handler(message: Message, session: AsyncSession) -> None:
  user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name)
  entries = await get_recent_entries(session, user_id=user.id, limit=30)
  await _send_main_menu(message, build_stats_text(entries))


@router.message(F.text == "Заснуть ночью")
async def night_start(message: Message, state: FSMContext) -> None:
  await state.clear()
  await state.set_state(NightFlow.slept)
  await message.answer("Сколько минут ты спал прошлой ночью?", reply_markup=main_menu)


@router.message(NightFlow.slept)
async def night_slept(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 0 or value > 24 * 60:
    await message.answer("Введи число минут от 0 до 1440.")
    return
  await state.update_data(slept=value)
  await state.set_state(NightFlow.quality)
  await message.answer("Оцени качество сна по шкале от 1 до 5.")


@router.message(NightFlow.quality)
async def night_quality(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 5:
    await message.answer("Введи число от 1 до 5.")
    return
  await state.update_data(quality=value)
  await state.set_state(NightFlow.sleepiness)
  await message.answer("Насколько ты сейчас сонный по шкале от 1 до 5?")


@router.message(NightFlow.sleepiness)
async def night_sleepiness(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 5:
    await message.answer("Введи число от 1 до 5.")
    return
  await state.update_data(sleepiness=value)
  await state.set_state(NightFlow.stress)
  await message.answer("Насколько ты сейчас напряжен или тревожен по шкале от 1 до 5?")


@router.message(NightFlow.stress)
async def night_stress(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 5:
    await message.answer("Введи число от 1 до 5.")
    return
  await state.update_data(stress=value)
  await state.set_state(NightFlow.free_time)
  await message.answer("Сколько минут у тебя есть на подготовку ко сну?")


@router.message(NightFlow.free_time)
async def night_free_time(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 120:
    await message.answer("Введи число минут от 1 до 120.")
    return
  await state.update_data(free_time=value)
  await state.set_state(NightFlow.alarm_minutes)
  await message.answer("Через сколько минут поставить будильник? Напиши 0, если не нужен.")


@router.message(NightFlow.alarm_minutes)
async def night_finish(
  message: Message,
  state: FSMContext,
  session: AsyncSession,
  session_factory: async_sessionmaker[AsyncSession],
  bot: Bot,
) -> None:
  alarm_minutes = _parse_int(message.text)
  if alarm_minutes is None or alarm_minutes < 0 or alarm_minutes > 24 * 60:
    await message.answer("Введи число минут от 0 до 1440.")
    return

  data = await state.get_data()
  user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name)
  recent_entries = await get_recent_entries(session, user_id=user.id, limit=7)

  recommendation = build_recommendation(
    request_type="night",
    slept_last_night_minutes=data["slept"],
    quality=data["quality"],
    sleepiness=data["sleepiness"],
    stress=data["stress"],
    free_time_minutes=data["free_time"],
    current_energy=None,
    recent_entries=recent_entries,
  )

  await create_session_request(
    session,
    user_id=user.id,
    requested_mode="night",
    free_time_minutes=data["free_time"],
    slept_last_night_minutes=data["slept"],
    current_energy_1_5=max(1, 6 - data["sleepiness"]),
    current_sleepiness_1_5=data["sleepiness"],
    current_stress_1_5=data["stress"],
    wants_alarm=alarm_minutes > 0,
    recommendation=recommendation,
  )

  result_text = await _build_plan_message(
    recommendation=recommendation,
    alarm_minutes=alarm_minutes,
    message=message,
    session=session,
    session_factory=session_factory,
    bot=bot,
    user_id=user.id,
  )
  await state.clear()
  await _send_main_menu(message, result_text)


@router.message(F.text == "Power Nap 10-20 мин")
async def power_nap_start(message: Message, state: FSMContext) -> None:
  await state.clear()
  await state.set_state(PowerNapFlow.slept)
  await message.answer(
    "Запускаем Power Nap. Сколько минут ты спал прошлой ночью?",
    reply_markup=main_menu,
  )


@router.message(PowerNapFlow.slept)
async def power_nap_slept(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 0 or value > 24 * 60:
    await message.answer("Введи число минут от 0 до 1440.")
    return
  await state.update_data(slept=value)
  await state.set_state(PowerNapFlow.feeling)
  await message.answer("Какой у тебя сейчас уровень энергии по шкале от 1 до 5?")


@router.message(PowerNapFlow.feeling)
async def power_nap_feeling(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 5:
    await message.answer("Введи число от 1 до 5.")
    return
  await state.update_data(feeling=value)
  await state.set_state(PowerNapFlow.sleepiness)
  await message.answer("Насколько ты сейчас сонный или уставший по шкале от 1 до 5?")


@router.message(PowerNapFlow.sleepiness)
async def power_nap_sleepiness(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 5:
    await message.answer("Введи число от 1 до 5.")
    return
  await state.update_data(sleepiness=value)
  await state.set_state(PowerNapFlow.free_time)
  await message.answer("Сколько свободных минут у тебя есть сейчас? Для power nap лучше 10-20 минут.")


@router.message(PowerNapFlow.free_time)
async def power_nap_free_time(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 60:
    await message.answer("Введи число минут от 1 до 60.")
    return
  await state.update_data(free_time=value)
  await state.set_state(PowerNapFlow.alarm_minutes)
  await message.answer("Через сколько минут поставить будильник? Напиши 0, если не нужен.")


@router.message(PowerNapFlow.alarm_minutes)
async def power_nap_finish(
  message: Message,
  state: FSMContext,
  session: AsyncSession,
  session_factory: async_sessionmaker[AsyncSession],
  bot: Bot,
) -> None:
  alarm_minutes = _parse_int(message.text)
  if alarm_minutes is None or alarm_minutes < 0 or alarm_minutes > 24 * 60:
    await message.answer("Введи число минут от 0 до 1440.")
    return

  data = await state.get_data()
  user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name)
  recent_entries = await get_recent_entries(session, user_id=user.id, limit=7)

  recommendation = build_recommendation(
    request_type="power_nap",
    slept_last_night_minutes=data["slept"],
    quality=3,
    sleepiness=data["sleepiness"],
    stress=2,
    free_time_minutes=data["free_time"],
    current_energy=data["feeling"],
    recent_entries=recent_entries,
  )

  await create_session_request(
    session,
    user_id=user.id,
    requested_mode="power_nap",
    free_time_minutes=data["free_time"],
    slept_last_night_minutes=data["slept"],
    current_energy_1_5=data["feeling"],
    current_sleepiness_1_5=data["sleepiness"],
    current_stress_1_5=2,
    wants_alarm=alarm_minutes > 0,
    recommendation=recommendation,
  )

  result_text = await _build_plan_message(
    recommendation=recommendation,
    alarm_minutes=alarm_minutes,
    message=message,
    session=session,
    session_factory=session_factory,
    bot=bot,
    user_id=user.id,
  )
  await state.clear()
  await _send_main_menu(message, result_text)


@router.message(F.text == "Дневной сон / перерыв")
async def day_start(message: Message, state: FSMContext) -> None:
  await state.clear()
  await state.set_state(DayFlow.slept)
  await message.answer("Сколько минут ты спал прошлой ночью?", reply_markup=main_menu)


@router.message(DayFlow.slept)
async def day_slept(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 0 or value > 24 * 60:
    await message.answer("Введи число минут от 0 до 1440.")
    return
  await state.update_data(slept=value)
  await state.set_state(DayFlow.feeling)
  await message.answer("Какой у тебя сейчас уровень энергии по шкале от 1 до 5?")


@router.message(DayFlow.feeling)
async def day_feeling(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 5:
    await message.answer("Введи число от 1 до 5.")
    return
  await state.update_data(feeling=value)
  await state.set_state(DayFlow.sleepiness)
  await message.answer("Насколько ты сейчас сонный или уставший по шкале от 1 до 5?")


@router.message(DayFlow.sleepiness)
async def day_sleepiness(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 5:
    await message.answer("Введи число от 1 до 5.")
    return
  await state.update_data(sleepiness=value)
  await state.set_state(DayFlow.free_time)
  await message.answer("Сколько свободных минут у тебя есть прямо сейчас?")


@router.message(DayFlow.free_time)
async def day_free_time(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 180:
    await message.answer("Введи число минут от 1 до 180.")
    return
  await state.update_data(free_time=value)
  await state.set_state(DayFlow.alarm_minutes)
  await message.answer("Через сколько минут поставить будильник? Напиши 0, если не нужен.")


@router.message(DayFlow.alarm_minutes)
async def day_finish(
  message: Message,
  state: FSMContext,
  session: AsyncSession,
  session_factory: async_sessionmaker[AsyncSession],
  bot: Bot,
) -> None:
  alarm_minutes = _parse_int(message.text)
  if alarm_minutes is None or alarm_minutes < 0 or alarm_minutes > 24 * 60:
    await message.answer("Введи число минут от 0 до 1440.")
    return

  data = await state.get_data()
  user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name)
  recent_entries = await get_recent_entries(session, user_id=user.id, limit=7)

  recommendation = build_recommendation(
    request_type="day",
    slept_last_night_minutes=data["slept"],
    quality=3,
    sleepiness=data["sleepiness"],
    stress=2,
    free_time_minutes=data["free_time"],
    current_energy=data["feeling"],
    recent_entries=recent_entries,
  )

  await create_session_request(
    session,
    user_id=user.id,
    requested_mode="day",
    free_time_minutes=data["free_time"],
    slept_last_night_minutes=data["slept"],
    current_energy_1_5=data["feeling"],
    current_sleepiness_1_5=data["sleepiness"],
    current_stress_1_5=2,
    wants_alarm=alarm_minutes > 0,
    recommendation=recommendation,
  )

  result_text = await _build_plan_message(
    recommendation=recommendation,
    alarm_minutes=alarm_minutes,
    message=message,
    session=session,
    session_factory=session_factory,
    bot=bot,
    user_id=user.id,
  )
  await state.clear()
  await _send_main_menu(message, result_text)


@router.message(F.text == "Я уже проснулся / как я поспал")
async def wake_start(message: Message, state: FSMContext) -> None:
  await state.clear()
  await state.set_state(WakeFlow.mode)
  await message.answer("Это был ночной сон или дневной сон?", reply_markup=sleep_mode_keyboard)


@router.message(WakeFlow.mode)
async def wake_mode(message: Message, state: FSMContext) -> None:
  mode_map = {
    "Ночной сон": "night_sleep",
    "Дневной сон": "day_nap",
  }
  mode = mode_map.get(message.text)
  if mode is None:
    await message.answer(
      "Выбери один из вариантов: Ночной сон или Дневной сон.",
      reply_markup=sleep_mode_keyboard,
    )
    return
  await state.update_data(mode=mode)
  await state.set_state(WakeFlow.duration)
  await message.answer("Сколько минут ты в итоге спал?", reply_markup=main_menu)


@router.message(WakeFlow.duration)
async def wake_duration(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 0 or value > 24 * 60:
    await message.answer("Введи число минут от 0 до 1440.")
    return
  await state.update_data(duration=value)
  await state.set_state(WakeFlow.quality)
  await message.answer("Как ты оцениваешь сон по шкале от 1 до 5?")


@router.message(WakeFlow.quality)
async def wake_quality(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 5:
    await message.answer("Введи число от 1 до 5.")
    return
  await state.update_data(quality=value)
  await state.set_state(WakeFlow.felt)
  await message.answer("Как ты чувствуешь себя после пробуждения по шкале от 1 до 5?")


@router.message(WakeFlow.felt)
async def wake_felt(message: Message, state: FSMContext) -> None:
  value = _parse_int(message.text)
  if value is None or value < 1 or value > 5:
    await message.answer("Введи число от 1 до 5.")
    return
  await state.update_data(felt=value)
  await state.set_state(WakeFlow.helpful)
  await message.answer("Насколько тебе помогла последняя рекомендация по шкале от 1 до 5?")


@router.message(WakeFlow.helpful)
async def wake_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
  helpful = _parse_int(message.text)
  if helpful is None or helpful < 1 or helpful > 5:
    await message.answer("Введи число от 1 до 5.")
    return

  data = await state.get_data()
  user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name)
  last_request = await get_last_session_request(session, user_id=user.id)

  await add_sleep_entry(
    session,
    user_id=user.id,
    mode=data["mode"],
    duration_minutes=data["duration"],
    quality=data["quality"],
    felt_after=data["felt"],
    stress_before=2,
    sleepiness_before=3,
    notes=f"helpful={helpful}",
  )
  await add_feedback(
    session,
    user_id=user.id,
    session_request_id=last_request.id if last_request is not None else None,
    was_helpful_1_5=helpful,
    user_followed_plan=True,
    comments=None,
  )

  await state.clear()
  await _send_main_menu(message, "Готово, я сохранил запись. Спасибо за обратную связь.")


@router.message(StateFilter(None), lambda message: bool(message.text and message.text.strip().isdigit()))
async def stop_alarm_by_code(message: Message, session: AsyncSession) -> None:
  code = message.text.strip()
  if len(code) != 4:
    return
  user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name)
  ok = await deactivate_alarm(session, user_id=user.id, code=code)
  if ok:
    await _send_main_menu(message, "Будильник выключен кодом.")


@router.message()
async def fallback_handler(message: Message) -> None:
  await _send_main_menu(
    message,
    "Я не понял сообщение. Выбери действие из меню или используй /help.",
  )
