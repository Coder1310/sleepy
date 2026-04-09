from aiogram.fsm.state import State, StatesGroup


class NightFlow(StatesGroup):
  slept = State()
  quality = State()
  sleepiness = State()
  stress = State()
  free_time = State()
  alarm_minutes = State()


class DayFlow(StatesGroup):
  slept = State()
  feeling = State()
  sleepiness = State()
  free_time = State()
  alarm_minutes = State()


class PowerNapFlow(StatesGroup):
  slept = State()
  feeling = State()
  sleepiness = State()
  free_time = State()
  alarm_minutes = State()


class WakeFlow(StatesGroup):
  mode = State()
  duration = State()
  quality = State()
  felt = State()
  helpful = State()
