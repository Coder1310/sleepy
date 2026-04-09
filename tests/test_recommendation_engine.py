from app.recommendation_engine import build_recommendation


def test_night_high_stress_returns_calm_protocol() -> None:
  rec = build_recommendation(
    request_type="night",
    slept_last_night_minutes=300,
    quality=2,
    sleepiness=4,
    stress=5,
    free_time_minutes=15,
  )
  assert rec.recommended_mode == "calm_night_protocol"


def test_short_day_window_returns_recovery_break() -> None:
  rec = build_recommendation(
    request_type="day",
    slept_last_night_minutes=360,
    quality=3,
    sleepiness=4,
    stress=2,
    free_time_minutes=8,
    current_energy=2,
  )
  assert rec.recommended_mode == "recovery_break"
