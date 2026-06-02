# OpenAI Image Telegram Bot

> Send a text prompt to a Telegram chat — get an AI-generated image back, in seconds.

A small, production-minded Telegram bot that turns text descriptions into images via the
**OpenAI Images API** (`gpt-image-2` by default). Built with `aiogram 3`, fully async, with a
whitelist access layer, a SQLite generation history, and zero hard-coded settings — everything
is driven by environment variables.

[![CI](https://github.com/chigerartem/openai-image-telegram-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/chigerartem/openai-image-telegram-bot/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![aiogram 3.x](https://img.shields.io/badge/aiogram-3.x-2CA5E0.svg)](https://docs.aiogram.dev/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

🇷🇺 [Русская версия README](README.ru.md)

---

## Demo

<!-- Placeholder mockup. Replace with a real screenshot/GIF: drop an image at docs/demo.png and update the src. -->
<p align="center">
  <img src="docs/demo.svg" alt="Bot demo: a text prompt turns into a generated image" width="320">
</p>

```
You:  a cosmonaut cat on the Moon, digital illustration, soft light
Bot:  🎨 Generating image…
Bot:  [image]  a cosmonaut cat on the Moon, digital illustration, soft light
```

---

## Features

- **Text → image in one message.** No commands, no menus — just describe what you want.
- **Configurable without touching code.** Model, size and quality are read from `.env`.
- **Whitelist access control.** Restrict the bot to specific Telegram IDs (or open it to everyone).
- **Generation history in SQLite.** Every attempt — success or failure — is recorded with a versioned migration runner.
- **Human-readable error handling.** Moderation rejections, quota limits and model-access errors are translated into clear messages.
- **Fully async** end to end (`aiogram` + `AsyncOpenAI` + `aiosqlite`).
- **Container-ready.** Ships with a slim, non-root `Dockerfile`.

---

## Architecture

```
┌──────────────┐   text prompt    ┌───────────────────────────────────────┐
│   Telegram   │ ───────────────► │              aiogram Dispatcher        │
│     user     │                  │                                        │
└──────────────┘                  │   ┌─────────────────────────────────┐  │
       ▲                          │   │ DbSessionMiddleware (inject conn)│  │
       │  generated PNG           │   ├─────────────────────────────────┤  │
       └───────────────────────── │   │ AccessMiddleware (whitelist)     │  │
                                  │   └─────────────────────────────────┘  │
                                  │                  │                      │
                                  │        ┌─────────▼──────────┐           │
                                  │        │   handlers/        │           │
                                  │        │  /start /help      │           │
                                  │        │  generate (prompt) │           │
                                  │        └─────┬───────┬──────┘           │
                                  └──────────────┼───────┼──────────────────┘
                                                 │       │
                                  ┌──────────────▼──┐ ┌──▼───────────────┐
                                  │ OpenAIImage\    │ │  SQLite          │
                                  │ Service         │ │  users +         │
                                  │ (Images API)    │ │  image_generations│
                                  └─────────────────┘ └──────────────────┘
```

The flow of a single request:

1. A non-command text message hits `handlers/generate.py`.
2. `AccessMiddleware` has already verified the sender is allowed (or the whitelist is empty).
3. The user is upserted into `users`; a "Generating…" status message is sent.
4. `OpenAIImageService.generate()` calls the Images API and returns raw PNG bytes.
5. The image is sent back as a photo; the attempt is logged to `image_generations`.

### Project layout

```
app/
├── main.py              # entry point — builds and runs the bot (long polling)
├── config.py            # frozen Config dataclass loaded from .env
├── handlers/
│   ├── commands.py      # /start, /help
│   └── generate.py      # prompt → image → reply
├── middlewares/
│   ├── access.py        # whitelist guard
│   └── db_session.py    # injects the DB connection into handlers
├── services/
│   └── openai_image.py  # thin async wrapper over the OpenAI Images API
└── db/
    ├── database.py      # connection + migration runner (WAL, FK on)
    ├── repository.py    # users + generation-history queries
    └── migrations/      # versioned .sql files, applied once and tracked
tests/                   # pytest unit tests
```

---

## Quick start (Windows / PowerShell)

```powershell
git clone https://github.com/chigerartem/openai-image-telegram-bot.git
cd openai-image-telegram-bot

py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env   # then fill in your keys in .env
python -m app.main
```

On macOS / Linux:

```bash
git clone https://github.com/chigerartem/openai-image-telegram-bot.git
cd openai-image-telegram-bot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then fill in your keys in .env
python -m app.main
```

You need two things to run it:

1. A **bot token** from [@BotFather](https://t.me/BotFather).
2. An **OpenAI API key** from [platform.openai.com](https://platform.openai.com/api-keys).

---

## Configuration (`.env`)

| Variable          | Description                                                          | Default            |
|-------------------|---------------------------------------------------------------------|--------------------|
| `BOT_TOKEN`       | Telegram bot token from [@BotFather](https://t.me/BotFather)        | — (required)       |
| `OPENAI_API_KEY`  | Key from platform.openai.com                                        | — (required)       |
| `OWNER_IDS`       | Allowed Telegram IDs (from [@userinfobot](https://t.me/userinfobot)), comma-separated | empty = open to everyone |
| `OPENAI_MODEL`    | `gpt-image-2` / `gpt-image-1.5` / `gpt-image-1` / `gpt-image-1-mini` | `gpt-image-2`      |
| `IMAGE_SIZE`      | `1024x1024` / `1024x1536` / `1536x1024`                              | `1024x1024`        |
| `IMAGE_QUALITY`   | `low` / `medium` / `high`                                            | `high`             |
| `DB_PATH`         | Path to the SQLite file                                              | `data/imagebot.db` |

---

## Tests

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

The image runs as a non-root user and writes its database to a mounted `/data` volume.

---

## Notes

- The top image models on some OpenAI accounts require **organization verification**. If the API
  returns an access error, set `OPENAI_MODEL=gpt-image-1-mini` in `.env`.
- Results are sent as Telegram photos (Telegram applies light preview compression).
- If `OWNER_IDS` is left empty, the bot logs a warning and serves **everyone** — set your ID to lock it down.

---

## Tech stack

`Python 3.12` · `aiogram 3` · `OpenAI Python SDK` · `aiosqlite` (SQLite + WAL) · `python-dotenv` · `Docker`

## License

[MIT](LICENSE) © Artem
