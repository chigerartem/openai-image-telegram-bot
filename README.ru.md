# OpenAI Image Telegram Bot

> Отправляешь текстовое описание в Telegram — за пару секунд получаешь сгенерированную картинку.

Небольшой, но «продакшен-ориентированный» Telegram-бот, который превращает текст в изображения
через **OpenAI Images API** (по умолчанию `gpt-image-2`). Написан на `aiogram 3`, полностью
асинхронный, с whitelist-доступом, историей генераций в SQLite и без единой захардкоженной
настройки — всё управляется через переменные окружения.

[![CI](https://github.com/chigerartem/openai-image-telegram-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/chigerartem/openai-image-telegram-bot/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![aiogram 3.x](https://img.shields.io/badge/aiogram-3.x-2CA5E0.svg)](https://docs.aiogram.dev/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

🇬🇧 [English README](README.md)

---

## Демо

<!-- Плейсхолдер-макет. Замени на реальный скриншот/GIF: положи картинку в docs/demo.png и поправь src. -->
<p align="center">
  <img src="docs/demo.svg" alt="Демо бота: текстовый промпт превращается в картинку" width="320">
</p>

```
Ты:   космонавт-кот на Луне, цифровая иллюстрация, мягкий свет
Бот:  🎨 Генерирую изображение…
Бот:  [картинка]  космонавт-кот на Луне, цифровая иллюстрация, мягкий свет
```

---

## Возможности

- **Текст → картинка одним сообщением.** Никаких команд и меню — просто опиши, что хочешь.
- **Настройка без правки кода.** Модель, размер и качество читаются из `.env`.
- **Контроль доступа по whitelist.** Можно ограничить бота конкретными Telegram ID (или открыть всем).
- **История генераций в SQLite.** Каждая попытка — успешная или с ошибкой — пишется в БД; миграции версионируются и применяются один раз.
- **Понятные ошибки.** Отказ модерации, превышение лимитов и проблемы доступа к модели переводятся в человеческие сообщения.
- **Полностью асинхронный** стек (`aiogram` + `AsyncOpenAI` + `aiosqlite`).
- **Готов к контейнеру.** В комплекте — лёгкий `Dockerfile` с запуском от непривилегированного пользователя.

---

## Архитектура

Путь одного запроса:

1. Текстовое сообщение (не команда) попадает в `handlers/generate.py`.
2. `AccessMiddleware` уже проверил, что отправитель в whitelist (или whitelist пуст).
3. Пользователь добавляется/обновляется в таблице `users`; отправляется статус «Генерирую…».
4. `OpenAIImageService.generate()` вызывает Images API и возвращает PNG-байты.
5. Картинка уходит обратно как фото; попытка логируется в `image_generations`.

### Структура проекта

```
app/
├── main.py              # точка входа — сборка и запуск бота (long polling)
├── config.py            # неизменяемый Config из .env
├── handlers/
│   ├── commands.py      # /start, /help
│   └── generate.py      # промпт → картинка → ответ
├── middlewares/
│   ├── access.py        # whitelist-доступ
│   └── db_session.py    # прокидывает соединение с БД в хендлеры
├── services/
│   └── openai_image.py  # тонкая async-обёртка над OpenAI Images API
└── db/
    ├── database.py      # соединение + runner миграций (WAL, FK on)
    ├── repository.py    # запросы по пользователям и истории
    └── migrations/      # версионированные .sql, применяются один раз
tests/                   # юнит-тесты на pytest
```

---

## Быстрый старт (Windows / PowerShell)

```powershell
git clone https://github.com/chigerartem/openai-image-telegram-bot.git
cd openai-image-telegram-bot

py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env   # затем впиши свои ключи в .env
python -m app.main
```

На macOS / Linux:

```bash
git clone https://github.com/chigerartem/openai-image-telegram-bot.git
cd openai-image-telegram-bot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # затем впиши свои ключи в .env
python -m app.main
```

Чтобы запустить, нужны две вещи:

1. **Токен бота** от [@BotFather](https://t.me/BotFather).
2. **Ключ OpenAI API** с [platform.openai.com](https://platform.openai.com/api-keys).

---

## Переменные окружения (`.env`)

| Переменная        | Описание                                                            | По умолчанию       |
|-------------------|---------------------------------------------------------------------|--------------------|
| `BOT_TOKEN`       | токен бота от [@BotFather](https://t.me/BotFather)                  | — (обязательно)    |
| `OPENAI_API_KEY`  | ключ с platform.openai.com                                          | — (обязательно)    |
| `OWNER_IDS`       | Telegram ID с доступом (узнать у [@userinfobot](https://t.me/userinfobot)), через запятую | пусто = доступ всем |
| `OPENAI_MODEL`    | `gpt-image-2` / `gpt-image-1.5` / `gpt-image-1` / `gpt-image-1-mini` | `gpt-image-2`      |
| `IMAGE_SIZE`      | `1024x1024` / `1024x1536` / `1536x1024`                              | `1024x1024`        |
| `IMAGE_QUALITY`   | `low` / `medium` / `high`                                            | `high`             |
| `DB_PATH`         | путь к файлу SQLite                                                  | `data/imagebot.db` |

---

## Тесты

```bash
pip install pytest
pytest
```

---

## Docker

```bash
docker build -t imagebot .
docker run --env-file .env -v "$PWD/data:/data" imagebot
```

Контейнер работает от непривилегированного пользователя и пишет базу в смонтированный том `/data`.

---

## Примечания

- Топовые image-модели у некоторых аккаунтов OpenAI требуют **верификации организации**. Если
  API вернёт ошибку доступа — поставь `OPENAI_MODEL=gpt-image-1-mini` в `.env`.
- Результат отправляется как фото Telegram (превью слегка сжимается).
- Если `OWNER_IDS` пуст, бот пишет предупреждение и пускает **всех** — укажи свой ID, чтобы закрыть доступ.

---

## Стек

`Python 3.12` · `aiogram 3` · `OpenAI Python SDK` · `aiosqlite` (SQLite + WAL) · `python-dotenv` · `Docker`

## Лицензия

[MIT](LICENSE) © Artem
