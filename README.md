# 🤖 Jarvis — AI-советник по 3D-печати

Telegram-бот на базе Claude AI, отслеживает MakerWorld и Etsy,
подсказывает что печатать для максимальных продаж.
Оптимизирован для деплоя на **Railway**.

---

## 📁 Структура проекта

```
jarvis_bot/
├── bot.py              — Telegram-бот + авто-отчёты (JobQueue)
├── agent.py            — AI-агент на базе Claude Sonnet
├── scraper.py          — парсинг MakerWorld + Etsy
├── config.py           — конфигурация из env-переменных
├── .env.example        — шаблон переменных окружения
├── requirements.txt
├── Procfile            — команда запуска для Railway
├── railway.json        — конфигурация Railway
└── .python-version     — версия Python (3.11)
```

---

## 🚀 Деплой на Railway (15 минут)

### Шаг 1 — Подготовь токены

**Telegram-бот:**
1. Напиши [@BotFather](https://t.me/BotFather) → `/newbot`
2. Скопируй токен: `7123456789:AAF...`

**Anthropic API:**
1. Зайди на https://console.anthropic.com → API Keys → Create Key
2. Скопируй ключ: `sk-ant-api03-...`

**Твой chat_id:**
1. Напиши [@userinfobot](https://t.me/userinfobot) в Telegram
2. Скопируй Id (число, например `123456789`)

---

### Шаг 2 — Загрузи код на GitHub

```bash
# Распакуй архив, зайди в папку
cd jarvis_bot

# Инициализируй git репозиторий
git init
git add .
git commit -m "Jarvis bot initial"

# Создай репо на github.com и свяжи
git remote add origin https://github.com/ТВО_ИМЯ/jarvis-bot.git
git push -u origin main
```

> ⚠️ **Не коммить .env файл!** Он уже в .gitignore.

---

### Шаг 3 — Деплой на Railway

1. Зайди на **https://railway.app** → New Project
2. **Deploy from GitHub repo** → выбери `jarvis-bot`
3. Railway автоматически найдёт `Procfile` и задеплоит

---

### Шаг 4 — Добавь переменные окружения

В Railway: открой проект → **Variables** → добавь:

| Variable | Value |
|----------|-------|
| `TELEGRAM_TOKEN` | токен от BotFather |
| `ANTHROPIC_API_KEY` | ключ от Anthropic |
| `TELEGRAM_CHAT_ID` | твой chat_id |
| `AUTO_ANALYZE_HOURS` | `6` |

После добавления Railway автоматически перезапустит бота.

---

### Шаг 5 — Проверь

Напиши боту `/start` — должен ответить приветствием.
Через 60 секунд придёт первый авто-отчёт (потом каждые N часов).

---

## 💬 Команды бота

| Команда | Описание |
|---------|----------|
| `/analyze` | Полный анализ рынка (~60 сек) |
| `/top` | Топ-10 моделей с обоснованием |
| `/niche organizer` | Анализ конкретной ниши |
| `/schedule` | Показать расписание отчётов |
| Любой текст | Вопрос к AI-аналитику |

---

## ⚙️ Настройка частоты отчётов

В Railway Variables измени `AUTO_ANALYZE_HOURS`:
- `6`  — каждые 6 часов (рекомендую)
- `12` — каждые 12 часов
- `24` — раз в сутки

---

## ❓ Частые проблемы

**Бот не отвечает после деплоя?**
→ Railway → Deployments → смотри логи. Скорее всего не заданы переменные.

**Etsy блокирует?**
→ Это нормально, Etsy часто блокирует скрапинг.
Бот всё равно отправит анализ на основе данных MakerWorld.
Для полного обхода — добавь переменную `HTTP_PROXY=http://user:pass@host:port`.

**Ошибка "claude API"?**
→ Проверь баланс на https://console.anthropic.com

**Railway останавливает сервис?**
→ На бесплатном плане Railway даёт $5/месяц — этого хватит на ~500 часов.
Если кончается — переключись на Render (бесплатный worker) или Fly.io.
