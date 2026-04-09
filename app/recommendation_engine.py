from __future__ import annotations

from statistics import mean

from app.models import SleepEntry
from app.schemas import Recommendation


TARGET_SLEEP_MINUTES = 8 * 60
LOW_SLEEP_THRESHOLD = 6 * 60


def _recent_average_minutes(entries: list[SleepEntry]) -> int | None:
  if not entries:
    return None
  return int(mean(item.duration_minutes for item in entries))


def build_recommendation(
  *,
  request_type: str,
  slept_last_night_minutes: int,
  quality: int,
  sleepiness: int,
  stress: int,
  free_time_minutes: int,
  current_energy: int | None = None,
  recent_entries: list[SleepEntry] | None = None,
) -> Recommendation:
  """
  Прозрачная эвристика без медицинских обещаний.

  request_type:
  - night
  - day
  - power_nap
  """
  recent_entries = recent_entries or []
  recent_avg = _recent_average_minutes(recent_entries)
  debt = max(0, TARGET_SLEEP_MINUTES - slept_last_night_minutes)
  long_running_sleep_deficit = recent_avg is not None and recent_avg < LOW_SLEEP_THRESHOLD

  if request_type == "night":
    if stress >= 4:
      return Recommendation(
        recommended_mode="calm_night_protocol",
        recommended_duration_minutes=min(max(free_time_minutes, 10), 15),
        explanation_for_user=(
          "Сейчас лучше сделать упор на успокоение и мягкий переход ко сну. "
          "При высоком напряжении короткий ритуал часто полезнее, чем попытка заставить себя уснуть."
        ),
        steps=[
          "Убери яркий свет и по возможности отложи экран на несколько минут",
          "Сделай 6 медленных вдохов и выдохов с длинным выдохом",
          "Расслабь челюсть, плечи и лоб",
          "Пройди короткий body scan от головы к стопам",
          "Если мысли крутятся, запиши 1-2 дела на завтра и вернись к дыханию",
        ],
        optional_audio_type="rain",
        suggest_alarm=True,
        confidence_label="high",
      )

    if debt >= 120 or quality <= 2 or long_running_sleep_deficit:
      return Recommendation(
        recommended_mode="standard_wind_down",
        recommended_duration_minutes=min(max(free_time_minutes, 5), 10),
        explanation_for_user=(
          "Похоже, у тебя есть недосып или сон в последние дни был не очень восстанавливающим. "
          "Сейчас лучше короткая спокойная подготовка ко сну без перегруза."
        ),
        steps=[
          "Сделай 5-6 спокойных циклов дыхания",
          "На 2 минуты расслабь шею, плечи и спину",
          "Оставь только тусклый свет",
          "Не спорь с мыслями и не оценивай, как быстро должен уснуть",
        ],
        optional_audio_type="forest",
        suggest_alarm=True,
        confidence_label="medium",
      )

    if free_time_minutes <= 3:
      return Recommendation(
        recommended_mode="ultra_short_wind_down",
        recommended_duration_minutes=max(free_time_minutes, 2),
        explanation_for_user="У тебя совсем мало времени, поэтому лучше сделать очень короткое, но реальное успокоение.",
        steps=[
          "Сделай 3 медленных вдоха и выдоха",
          "Ослабь напряжение в лице и плечах",
          "Погаси лишний свет и отложи телефон",
        ],
        optional_audio_type="silence",
        suggest_alarm=True,
        confidence_label="medium",
      )

    return Recommendation(
      recommended_mode="short_wind_down",
      recommended_duration_minutes=min(max(free_time_minutes, 4), 7),
      explanation_for_user="Сейчас тебе подойдет короткий вечерний ритуал без лишней сложности.",
      steps=[
        "Сделай 5 спокойных вдохов и выдохов",
        "Расслабь лицо, шею и плечи",
        "На пару минут переведи внимание на дыхание или ощущения в теле",
      ],
      optional_audio_type="silence",
      suggest_alarm=True,
      confidence_label="medium",
    )

  if request_type == "power_nap":
    if free_time_minutes < 10:
      return Recommendation(
        recommended_mode="power_nap_too_short_switch_to_reset",
        recommended_duration_minutes=max(3, min(free_time_minutes, 8)),
        explanation_for_user=(
          "Для нормального power nap обычно лучше иметь хотя бы 10 минут окна. "
          "Сейчас логичнее сделать короткий reset без давления на сон."
        ),
        steps=[
          "Закрой глаза на 3-8 минут",
          "Сделай медленное дыхание",
          "Не пытайся обязательно уснуть",
        ],
        optional_audio_type="pink_noise",
        suggest_alarm=False,
        confidence_label="high",
      )

    duration = 20 if free_time_minutes >= 20 else free_time_minutes
    if sleepiness >= 4 or slept_last_night_minutes < LOW_SLEEP_THRESHOLD or (current_energy is not None and current_energy <= 2):
      return Recommendation(
        recommended_mode="power_nap_10_20",
        recommended_duration_minutes=duration,
        explanation_for_user=(
          "Окно хорошо подходит для power nap. Цель - быстро снизить сонливость и немного восстановиться, "
          "а не обязательно глубоко уснуть."
        ),
        steps=[
          "Поставь будильник так, чтобы уложиться в 10-20 минут",
          "Ляг или сядь с хорошей опорой",
          "Сделай 5 спокойных вдохов и выдохов",
          "Если сон не приходит, просто полежи с закрытыми глазами",
          "После сигнала встань не сразу, дай себе 1-2 минуты на включение",
        ],
        optional_audio_type="rain",
        suggest_alarm=True,
        confidence_label="high",
      )

    return Recommendation(
      recommended_mode="light_power_nap",
      recommended_duration_minutes=min(duration, 15),
      explanation_for_user=(
        "Даже если сонливость не очень высокая, короткий power nap или тихая пауза на 10-15 минут могут помочь "
        "снизить усталость без тяжелого пробуждения."
      ),
      steps=[
        "Выдели 10-15 минут в тихом месте",
        "Закрой глаза и ослабь напряжение в лице и плечах",
        "Не листай телефон до конца паузы",
        "После паузы выпей воды и немного разомнись",
      ],
      optional_audio_type="forest",
      suggest_alarm=True,
      confidence_label="medium",
    )

  if free_time_minutes < 10:
    return Recommendation(
      recommended_mode="recovery_break",
      recommended_duration_minutes=max(3, min(free_time_minutes, 8)),
      explanation_for_user=(
        "Времени мало, поэтому лучше не давить на себя попыткой заснуть, "
        "а сделать короткую восстанавливающую паузу."
      ),
      steps=[
        "Сядь или ляг удобно и закрой глаза",
        "Сделай медленное дыхание 3-7 минут",
        "Не проверяй уведомления до конца паузы",
      ],
      optional_audio_type="pink_noise",
      suggest_alarm=False,
      confidence_label="high",
    )

  if free_time_minutes <= 30:
    return Recommendation(
      recommended_mode="guided_nap_attempt",
      recommended_duration_minutes=min(free_time_minutes, 25),
      explanation_for_user=(
        "Окно подходит для короткого дневного сна или тихой сессии отдыха. "
        "Не заставляй себя уснуть, цель - снизить усталость."
      ),
      steps=[
        "Поставь будильник на конец окна",
        "Ляг или сядь с опорой",
        "Сконцентрируйся на дыхании и отпусти ожидания",
        "После пробуждения медленно встань и выпей воды",
      ],
      optional_audio_type="rain",
      suggest_alarm=True,
      confidence_label="medium",
    )

  if current_energy is not None and current_energy <= 2:
    return Recommendation(
      recommended_mode="long_rest_session",
      recommended_duration_minutes=min(free_time_minutes, 40),
      explanation_for_user=(
        "Энергии сейчас мало, поэтому можно взять более длинное окно на восстановление. "
        "Но лучше воспринимать это как отдых, а не как гарантию идеального сна."
      ),
      steps=[
        "Отключи лишние уведомления",
        "Устрой тихую сессию 20-40 минут",
        "После паузы немного пройдись и сделай несколько глубоких вдохов",
      ],
      optional_audio_type="forest",
      suggest_alarm=True,
      confidence_label="medium",
    )

  return Recommendation(
    recommended_mode="extended_recovery_break",
    recommended_duration_minutes=min(free_time_minutes, 20),
    explanation_for_user="У тебя достаточно времени на нормальную восстановительную паузу без спешки.",
    steps=[
      "Уйди от экрана на 10-20 минут",
      "Сделай спокойное дыхание или короткую медитацию",
      "Не пытайся выжать максимум пользы, цель - немного снизить усталость",
    ],
    optional_audio_type="soft_multiaudio",
    suggest_alarm=True,
    confidence_label="medium",
  )
