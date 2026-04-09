from app.services.alarm_service import generate_alarm_code


def test_alarm_code_is_4_digits() -> None:
  code = generate_alarm_code()
  assert len(code) == 4
  assert code.isdigit()
