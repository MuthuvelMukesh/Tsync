# Tsync — Modular Intelligence & Incident Tracking Engine

A production-grade, modular, layered, and independently testable intelligence engine. Collects messages from multiple sources (Telegram, RSS, APIs), normalizes and scores them, clusters them into evolving incidents, enriches them with AI intelligence, and delivers multi-channel digests and real-time alerts.

---

## 🏗️ Architecture & Separation of Concerns

Tsync strictly follows **Clean Architecture, Dependency Inversion, and Separation of Concerns**:

```
                       ┌─────────────────────────┐
                       │      Domain Layer       │
                       │ (Pure Entities & Events)│
                       └────────────▲────────────┘
                                    │
                       ┌────────────┴────────────┐
                       │     Services Layer      │
                       │ (Orchestrators & Rules) │
                       └────────────▲────────────┘
                                    │
                       ┌────────────┴────────────┐
                       │     Workflows Layer     │
                       │   (Pipeline Sequences)  │
                       └────────────▲────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
┌────────┴────────┐        ┌────────┴────────┐        ┌────────┴────────┐
│  Ingestion      │        │  Storage        │        │ Notifications   │
│  (Telethon/RSS) │        │  (PostgreSQL/   │        │ (WhatsApp/      │
│                 │        │   SQLite Async) │        │  Telegram Bot)  │
└─────────────────┘        └─────────────────┘        └─────────────────┘
```

### Key Architectural Invariants
1. **Domain Independence**: The `app/domain` package imports ZERO external frameworks, database ORMs, or network libraries (`SQLAlchemy`, `httpx`, `Telethon`, `OpenRouter`, `os.getenv`).
2. **Repository Abstractions**: All persistence is accessed via protocols (`MessageRepository`, `IncidentRepository`, `SourceRepository`, `EntityRepository`). The engine runs equally against SQLite, PostgreSQL, or test mocks.
3. **Pluggable AI & Ingestion**: External providers (`OpenRouter`, `Telegram`) implement clean interfaces (`AIProvider`, `MessageSource`).
4. **Policy-Driven Notifications**: Notification decisions (`NotificationPolicy`) are decoupled from delivery adapters (`WhatsAppNotificationProvider`, `TelegramNotificationProvider`).
5. **Thin Adapters**: The Telegram bot and CLI scripts are thin adapters delegating all business operations to services.

---

## 📂 Target Structure

```text
tsync/
│
├── app/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   ├── incidents.py
│   │   ├── messages.py
│   │   ├── claims.py
│   │   └── events.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── telegram.py
│   │   └── service.py
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── filtering.py
│   │   ├── normalization.py
│   │   ├── categorization.py
│   │   └── scoring.py
│   ├── incidents/
│   │   ├── __init__.py
│   │   ├── detector.py
│   │   ├── matcher.py
│   │   ├── updater.py
│   │   ├── clustering.py
│   │   ├── timeline.py
│   │   ├── contradictions.py
│   │   └── relationships.py
│   ├── intelligence/
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   ├── summarizer.py
│   │   ├── entities.py
│   │   ├── confidence.py
│   │   └── prompts.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── openrouter.py
│   │   ├── models.py
│   │   └── retry.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repositories/
│   │       ├── messages.py
│   │       ├── incidents.py
│   │       ├── sources.py
│   │       ├── entities.py
│   │       └── notifications.py
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── whatsapp.py
│   │   ├── telegram.py
│   │   └── dispatcher.py
│   ├── bots/
│   │   ├── __init__.py
│   │   ├── telegram/
│   │   │   ├── bot.py
│   │   │   ├── handlers.py
│   │   │   ├── commands.py
│   │   │   └── auth.py
│   │   └── common/
│   │       └── formatting.py
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── hourly.py
│   │   ├── daily.py
│   │   └── formatters.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── incident_service.py
│   │   ├── search_service.py
│   │   ├── briefing_service.py
│   │   └── status_service.py
│   └── workflows/
│       ├── __init__.py
│       ├── hourly.py
│       ├── breaking.py
│       └── backfill.py
│
├── scripts/
│   ├── hourly.py
│   ├── bot.py
│   └── migrate.py
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── incidents/
│   │   ├── intelligence/
│   │   ├── processing/
│   │   └── services/
│   ├── integration/
│   │   ├── storage/
│   │   ├── telegram/
│   │   ├── whatsapp/
│   │   └── ai/
│   └── e2e/
│       └── incident_lifecycle/
│
├── migrations/
│   └── init_schema.sql
├── config/
│   └── channels.json
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

---

## ⚡ Quick Start

### 1. Installation

```bash
git clone https://github.com/MuthuvelMukesh/Tsync.git
cd Tsync
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- `DATABASE_URL`: `sqlite+aiosqlite:///./tsync.db` (default local) or `postgresql+asyncpg://user:pass@host:5432/tsync`
- `OPENROUTER_API_KEY`: Key from [openrouter.ai](https://openrouter.ai)
- `TELEGRAM_API_ID` & `TELEGRAM_API_HASH`: From [my.telegram.org](https://my.telegram.org)
- `TELEGRAM_BOT_TOKEN`: From [@BotFather](https://t.me/BotFather)
- `WHATSAPP_ACCESS_TOKEN` & `WHATSAPP_PHONE_NUMBER_ID`: From Meta Cloud API

### 3. Initialize Database

```bash
python scripts/migrate.py
# or
python main.py --migrate
```

### 4. Run Workflows

```bash
# Demo mode (zero external credentials required)
python main.py --demo

# Standard hourly intelligence cycle (ingestion + incident matching + reporting)
python main.py

# Start the Telegram Bot daemon
python main.py --bot
# or
python scripts/bot.py
```

---

## 🔄 Incident Lifecycle

```
NEW
 │  (single source / initial event)
 ▼
DEVELOPING
 │  ├── multi-source corroboration
 │  ├── new claims extracted
 │  ├── contradiction detected
 │  └── escalation of impact score
 ▼
MONITORING
 │  (active tracking of stabilized situation)
 ▼
RESOLVED
 │  (official closure / stabilized)
 ▼
ARCHIVED
```

---

## 🧪 Test Suite

Run the full suite of unit, integration, and end-to-end tests:

```bash
pytest tests -v
```

All 56 tests execute across:
- **Unit**: Domain lifecycle, incidents, intelligence, processing, scoring, and services.
- **Integration**: Repositories with in-memory SQLite, Telegram/WhatsApp HTTP adapters, OpenRouter adapter.
- **E2E**: Full incident lifecycle from message arrival through multi-source progression, timeline compilation, and digest generation.

---

## 🐳 Docker Deployment

Build and run containerized:

```bash
docker build -t tsync .
docker run --env-file .env tsync
```

---

## 📄 License

MIT License.
