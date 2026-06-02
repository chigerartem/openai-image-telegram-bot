# OpenAI Image Telegram Bot

> Send a text prompt to a Telegram chat — get an AI-generated image back, in seconds.

A small, production-minded Telegram bot that turns text descriptions — or a text prompt plus a
**reference photo** — into images via the **OpenAI Images API** (`gpt-image-2` by default). Built
with `aiogram 3`, fully async, with an inline `/settings` menu for format / quality / model,
per-user settings, a whitelist access layer, and a SQLite generation history.

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

- **Text → image in one message.** Just describe what you want.
- **Reference images (image-to-image).** Attach a photo with a caption and the bot uses it as a
  reference via the OpenAI `images.edit` endpoint — the part the plain `generate` call can't do.
- **Format control.** Pick `1:1`, `3:2`, `2:3`, `16:9`, `9:16`, `Auto`, or type a **custom resolution**
  like `1920×1080`. Widescreen and custom sizes are produced by generating the nearest native size
  and cropping/fitting with Pillow.
- **Inline settings menu (`/settings`).** Buttons to switch aspect ratio, quality, model, and
  reference fidelity — no need to touch `.env` or restart.
- **Per-user settings** persisted in SQLite — every user keeps their own format/quality/model.
- **Whitelist access control.** Restrict the bot to specific Telegram IDs (or open it to everyone).
- **Generation history in SQLite.** Every attempt — success or failure — is recorded with a versioned migration runner.
- **Human-readable error handling.** Moderation rejections, quota limits and model-access errors are translated into clear messages.
- **Fully async** end to end (`aiogram` + `AsyncOpenAI` + `aiosqlite`).
- **Container-ready.** Ships with a slim, non-root `Dockerfile`.

## Usage

| You send | The bot does |
|----------|--------------|
| A text description | Generates an image from the prompt (`images.generate`) |
| A photo **with a caption** | Uses the photo as a reference and the caption as the instruction (`images.edit`) |
| `/settings` | Opens an inline menu: format · quality · model · reference fidelity |

Formats map to the API like this: `1:1 / 3:2 / 2:3` are native sizes (lossless); `16:9` and `9:16`
are center-cropped from the nearest native size; a custom `W×H` is generated at the nearest native
size and then cover-cropped + resized to the exact pixels.

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

1. A text prompt (or a photo + caption) hits `handlers/generate.py`.
2. `AccessMiddleware` has already verified the sender is allowed (or the whitelist is empty).
3. The user is upserted; their per-user settings are loaded and turned into a **render plan**
   (`presets.plan_render` → API size + optional crop/fit).
4. `OpenAIImageService.generate()` (text) or `.edit()` (with the reference photo) calls the Images
   API and returns raw PNG bytes.
5. `image_processing` applies the crop/fit for `16:9`, `9:16` or a custom resolution (off the event
   loop via `asyncio.to_thread`).
6. The image is sent back as a photo; the attempt is logged to `image_generations`.

### Project layout

```
app/
├── main.py                  # entry point — builds and runs the bot (long polling)
├── config.py                # frozen Config dataclass loaded from .env
├── presets.py               # formats/quality/model tables + render planning
├── keyboards.py             # inline menus for /settings
├── handlers/
│   ├── commands.py          # /start, /help
│   ├── settings.py          # /settings menu + callbacks + custom-size FSM
│   └── generate.py          # prompt / photo-reference → image → reply
├── middlewares/
│   ├── access.py            # whitelist guard (messages + callbacks)
│   └── db_session.py        # injects the DB connection into handlers
├── services/
│   ├── openai_image.py      # async wrapper over images.generate + images.edit
│   └── image_processing.py  # Pillow: crop-to-ratio / fit-to-size / to-png
└── db/
    ├── database.py          # connection + migration runner (WAL, FK on)
    ├── repository.py        # users, history and per-user settings
    └── migrations/          # versioned .sql files, applied once and tracked
tests/                       # pytest unit tests
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
| `OPENAI_MODEL`    | Default model for new users (everyone can change it in `/settings`) | `gpt-image-2`      |
| `DB_PATH`         | Path to the SQLite file                                              | `data/imagebot.db` |

> Format, quality, model and reference fidelity are **per-user** and live in the database —
> changed at runtime through the `/settings` menu, not in `.env`.

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
- **Reference fidelity** (`input_fidelity`) is only honored by some models — `gpt-image-1` supports
  it, while `gpt-image-2` does not. The bot sends the parameter and transparently retries without it
  when the model rejects it, so the setting never breaks a request; it simply has no effect on models
  that ignore it.
- Results are sent as Telegram photos (Telegram applies light preview compression).
- If `OWNER_IDS` is left empty, the bot logs a warning and serves **everyone** — set your ID to lock it down.

---

## Tech stack

`Python 3.12` · `aiogram 3` · `OpenAI Python SDK` · `aiosqlite` (SQLite + WAL) · `python-dotenv` · `Docker`

## License

[MIT](LICENSE) © Artem
