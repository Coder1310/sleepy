from __future__ import annotations

from collections import Counter

from app.models import SleepEntry


def build_history_text(entries: list[SleepEntry]) -> str:
  if not entries:
    return "История пока пуста."

  lines = ["Последние записи:"]
  for item in entries:
    lines.append(
      f"- {item.entry_date}: {item.mode}, {item.duration_minutes} мин, "
      f"качество {item.subjective_sleep_quality_1_5}/5, "
      f"самочувствие {item.felt_after_waking_1_5}/5"
    )
  return "\n".join(lines)


def build_stats_text(entries: list[SleepEntry]) -> str:
  if not entries:
    return "Пока нет данных. Добавь хотя бы одну запись о сне."

  avg_duration = sum(item.duration_minutes for item in entries) / len(entries)
  avg_quality = sum(item.subjective_sleep_quality_1_5 for item in entries) / len(entries)
  avg_feeling = sum(item.felt_after_waking_1_5 for item in entries) / len(entries)
  mode_counter = Counter(item.mode for item in entries)

  lines = [
    "Твоя краткая статистика:",
    f"- Средняя длительность сна: {avg_duration:.0f} мин",
    f"- Средняя оценка качества сна: {avg_quality:.1f}/5",
    f"- Среднее самочувствие после пробуждения: {avg_feeling:.1f}/5",
    f"- Чаще всего ты отмечал режим: {mode_counter.most_common(1)[0][0]}",
  ]

  if avg_duration < 6 * 60:
    lines.append("- Последние записи намекают на заметный недосып")
  elif avg_duration < 7 * 60:
    lines.append("- Ты спишь меньше типичного рекомендуемого диапазона")
  else:
    lines.append("- По длительности сон выглядит относительно неплохо")

  if avg_quality < 3:
    lines.append("- По субъективной оценке сон пока не очень восстанавливающий")
  else:
    lines.append("- По субъективной оценке сон в целом выглядит нормально")

  return "\n".join(lines)
