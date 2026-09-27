# 💅 Beauty CRM

CRM-система с Telegram-ботом для бьюти-студии (Кыргызстан).

## 📱 О проекте

Полнофункциональная CRM-система для управления бьюти-студией:
- Онлайн-запись клиентов через Telegram-бота
- Управление услугами и ценами
- Настройка графика работы
- База клиентов (CRM)
- Журнал записей
- Система бонусов и акций

## 🔧 Технологии

### Backend
- **Python 3.10+**
- **FastAPI** — веб-фреймворк
- **uvicorn** — ASGI-сервер
- **PostgreSQL 16** — база данных
- **Redis 7** — кэширование
- **Celery** — фоновые задачи
- **Docker** — контейнеризация

### Telegram Bot
- **python-telegram-bot** — библиотека для Telegram API
- **ConversationHandler** — FSM для диалогов

## 📦 Структура

```
beautycrm/
├── backend/                 # FastAPI приложение
│   ├── app/
│   │   ├── main.py          # Точка входа
│   │   ├── models/          # Модели данных
│   │   ├── routers/         # API эндпоинты
│   │   └── tasks/           # Celery задачи
│   └── Dockerfile
├── frontend/                # Веб-интерфейс
├── twa/                     # Telegram Web App
├── docker-compose.yml       # Оркестрация
├── pure_bot.py              # Standalone Telegram бот
├── .env.example             # Шаблон переменных окружения
└── README.md
```

## 🚀 Запуск

### Docker Compose (рекомендуется)
```bash
cp .env.example .env
docker-compose up -d
```

### Ручной запуск

#### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Telegram Bot
```bash
pip install python-telegram-bot
python pure_bot.py --token "YOUR_TOKEN" --admin-id YOUR_ADMIN_ID
```

## ⚙️ Настройка

### Переменные окружения
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/beautycrm
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
BOT_TOKEN=your-telegram-bot-token
ADMIN_ID=your-telegram-id
```

## 💡 Функционал

### Для клиентов
- 📱 Онлайн-запись через Telegram-бот
- 📋 Просмотр своих записей
- ❌ Отмена записи
- 🎁 Акции и бонусная система

### Для мастера/администратора
- 💅 Управление услугами (добавление, удаление, редактирование)
- ⏰ Настройка график работы (Пн-Вс)
- 📅 Журнал записей
- 👥 База клиентов с метриками LTV
- 📊 Статистика и аналитика

## 💰 Валюта

Все расчёты в сомах (KGS) — официальная валюта Кыргызстана.

## 📄 Лицензия

MIT
