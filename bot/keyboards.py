from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


main_menu = ReplyKeyboardMarkup(
  keyboard=[
    [KeyboardButton(text="Заснуть ночью")],
    [KeyboardButton(text="Power Nap 10-20 мин")],
    [KeyboardButton(text="Дневной сон / перерыв")],
    [KeyboardButton(text="Я уже проснулся / как я поспал")],
    [KeyboardButton(text="История"), KeyboardButton(text="Статистика")],
    [KeyboardButton(text="Настройки"), KeyboardButton(text="Premium")],
    [KeyboardButton(text="Помощь"), KeyboardButton(text="В меню")],
  ],
  resize_keyboard=True,
  input_field_placeholder="Выбери действие",
)


sleep_mode_keyboard = ReplyKeyboardMarkup(
  keyboard=[
    [KeyboardButton(text="Ночной сон"), KeyboardButton(text="Дневной сон")],
    [KeyboardButton(text="В меню")],
  ],
  resize_keyboard=True,
)
