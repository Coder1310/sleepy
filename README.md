# Sleep Support Bot

Полностью рабочий MVP Telegram-бота для:
- вечерней подготовки ко сну
- короткого дневного восстановления
- чек-ина после сна
- истории и статистики
- будильника внутри Telegram

## Стек
- Python 3.12+
- aiogram 3
- SQLAlchemy async
- SQLite
- APScheduler

## Структура
```text
sleep_support_bot/
  app/
    config.py
    db.py
    models.py
    schemas.py
    recommendation_engine.py
    scheduler.py
    services/
      alarm_service.py
      session_service.py
      sleep_service.py
      stats_service.py
      user_service.py
  bot/
    handlers.py
    keyboards.py
    states.py
    texts.py
  tests/
  main.py
  requirements.txt
  .env.example
  Dockerfile
  docker-compose.yml
```

## Что умеет
1. Сценарий "Заснуть ночью"
2. Сценарий "Дневной сон / перерыв"
3. Сохранение записи после сна
4. История последних записей
5. Простая статистика
6. Будильник с кодом выключения
7. Восстановление активных будильников после перезапуска приложения

## Ограничения
- Бот не заменяет врача
- Это не медицинское приложение
- Premium и расширенные настройки пока оставлены как базовые экраны

## Локальный запуск
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Заполни `.env`:
```env
BOT_TOKEN=твой_токен_бота
DATABASE_URL=sqlite+aiosqlite:///./sleep_bot.db
DEFAULT_TIMEZONE=Europe/Moscow
```

Дальше:
```bash
python main.py
```

## Docker
```bash
cp .env.example .env
docker compose up --build
```

## Тесты
```bash
pytest
```

## Важная заметка по будильнику
Код выключения бот присылает в сообщении при срабатывании будильника.
Остановить можно:
```bash
/stop_alarm 1234
```
или просто отправив в чат сам код.

## Что можно развить дальше
- отдельные пользовательские настройки timezone
- inline-кнопки вместо части текстового ввода
- richer content для медитаций и аудио
- weekly insights
- подписки и feature flags
- дедлайны и расписание как следующий этап
