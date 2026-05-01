# Telegram Content Bot

AI-powered Telegram bot that automatically generates and publishes posts to channels.

## Features

- **Automatic content generation:** collects information from web (DuckDuckGo), RSS feeds, and other Telegram channels — runs it through AI to produce a polished post.
- **Custom system prompts:** users can configure how the AI writes (tone, length, language, hashtags).
- **Channel style mimicking** *(Premium):* analyzes the last N posts of the target channel and writes in the same style.
- **Image handling:** searches Unsplash/Pexels for a fitting photo first; if nothing matches, generates one with Pollinations.ai (DALL·E / SD optional).
- **Time-period filtering:** pull news from the last hour / day / week / month.
- **Subscription tiers** (paid via Telegram Stars):
  - **Free** — 3 posts/month, basic model, watermark + bot promo every 5 posts in the channel.
  - **Pro** — 50 posts/month, image generation, no in-channel promo.
  - **Premium** — unlimited posts, custom system prompt, channel-style analysis, no watermark.
- **Smart watermarking:** visible signature + invisible zero-width markers. The bot detects when a free user manually deletes the signature and restores it. When a user upgrades, all watermarks are removed.
- **Self-promotion:** the bot periodically writes promo posts about itself — both in client channels (free tier) and in its own showcase channel.
- **Multi-language UI:** RU / EN / ES.
- **Publishing modes:** auto-publish or preview-and-approve.

## Tech Stack

- **Python 3.12** + **aiogram 3** (Telegram Bot API)
- **Telethon** (parsing other Telegram channels)
- **PostgreSQL 16** + **SQLAlchemy 2** + **Alembic** (data + migrations)
- **Redis** + **arq** (background queue + scheduling)
- **Google Gemini** (default text AI — free tier) with provider-agnostic adapter
- **Pollinations.ai** (default image generation — free, no API key)
- **DuckDuckGo Search** + **feedparser** (web/RSS sources)
- **Pillow** (image processing)
- **Docker + docker-compose** (deployment)

## Quick Start

### 1. Get free credentials

| Service | Where | Required for |
|---|---|---|
| Bot Token | https://t.me/BotFather | Always |
| Telegram API ID/Hash | https://my.telegram.org | Parsing TG channels as sources |
| Gemini API Key | https://aistudio.google.com/apikey | Default AI provider |
| Unsplash Access Key | https://unsplash.com/developers | Stock images (optional) |
| Pexels API Key | https://www.pexels.com/api/ | Stock images (optional) |
| Groq API Key | https://console.groq.com/keys | Alternative free AI (optional) |

### 2. Configure

```bash
cp .env.example .env
# fill in BOT_TOKEN, GEMINI_API_KEY, TELEGRAM_API_ID, TELEGRAM_API_HASH at minimum
```

### 3. Run with Docker

```bash
docker compose up -d --build
docker compose exec bot alembic upgrade head
```

### 4. Talk to your bot

Open the bot in Telegram, hit `/start`, follow the onboarding.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Compile translations
./scripts/compile_translations.sh

# Run database migrations
alembic upgrade head

# Run the bot
python -m src.main

# Run the worker (in another terminal)
arq src.workers.tasks.WorkerSettings
```

### Tests / lint / typecheck

```bash
pytest
ruff check .
ruff format --check .
mypy src
```

## Project Structure

```
telegram-content-bot/
├── alembic/                 # database migrations
├── docker-compose.yml
├── Dockerfile
├── locales/                 # translations (ru/en/es)
├── pyproject.toml
├── scripts/                 # helper scripts
├── src/
│   ├── bot/                 # aiogram handlers, keyboards, middleware
│   ├── core/                # config, db, i18n, logging
│   ├── models/              # SQLAlchemy models
│   ├── services/
│   │   ├── ai/              # provider-agnostic AI client (Gemini default)
│   │   ├── collectors/      # web search, RSS, Telegram channels
│   │   ├── images/          # stocks + Pollinations generation
│   │   ├── style_analyzer/  # channel style fingerprinting (Premium)
│   │   ├── watermark/       # visible + zero-width watermarks
│   │   ├── publisher/       # post composition + publishing
│   │   ├── scanner/         # detect manually-removed watermarks
│   │   └── payments/        # Telegram Stars subscriptions
│   ├── workers/             # background arq tasks
│   └── main.py
└── tests/
```

## License

MIT
