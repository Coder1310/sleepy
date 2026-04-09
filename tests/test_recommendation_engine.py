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
  )
  assert rec.recommended_mode == "recovery_break"


def test_power_nap_window_returns_explicit_power_nap_mode() -> None:
  rec = build_recommendation(
    request_type="power_nap",
    slept_last_night_minutes=320,
    quality=3,
    sleepiness=5,
    stress=2,
    free_time_minutes=20,
    current_energy=2,
  )
  assert rec.recommended_mode == "power_nap_10_20"
