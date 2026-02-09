# Telegram Idle Business Game

Игра-симулятор бизнеса (ресторана быстрого питания) для Telegram с Web App интерфейсом.

## Технологический стек

### Backend
- Python 3.10
- aiogram 3.x (Telegram Bot API)
- SQLite3 (база данных)
- aiohttp (веб-сервер для Web App)
- pydantic (валидация данных)

### Frontend (Web App)
- React 18
- TypeScript
- Vite (сборщик)
- Tailwind CSS (стилизация)
- Zustand (управление состоянием)

## Структура проекта

```
telegram-idle-game/
├── backend/
│   ├── bot/                    # Telegram бот
│   ├── webapp/                 # API для Web App
│   ├── database/              # Работа с БД
│   ├── game/                  # Игровая логика
│   ├── config/                # Конфигурация
│   └── main.py               # Точка входа
├── frontend/                  # Web App (React)
├── docs/                     # Документация
└── requirements.txt          # Python зависимости
```

## Основные возможности

- 🏪 Управление рестораном быстрого питания
- 💰 Пассивный доход (работает офлайн)
- 🎮 Мини-игры для бонусов
- 📈 Улучшения оборудования и персонала
- 📊 Статистика в боте и Web App
- 👥 Групповые рейтинги
- 🏆 Достижения и лидерборды

## Установка и запуск


