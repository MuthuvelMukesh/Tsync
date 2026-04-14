# Tsync — Telegram Intelligence Engine

A production-ready, modular system that collects messages from Telegram channels, processes them through a hybrid AI pipeline, and generates clean intelligence reports.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen)

---

## ⚡ Features

- **Telegram Ingestion** — Collects messages from configured channels via Telethon
- **Hybrid Categorization** — Rule-based first, AI fallback only when needed
- **Dynamic Selection** — Adaptive thresholds (no fixed Top-N limits)
- **Intelligence Generation** — AI-powered What + Why analysis for selected items
- **Trend Detection** — N-gram analysis for trending topics and patterns
- **Beautiful Reports** — Dark-themed HTML + plain text output
- **Freemium Optimized** — Minimal API usage through smart filtering

---

## 🏗️ Architecture

```
Telegram Channels
       │
       ▼
┌─────────────┐
│  Ingestion   │  ← Telethon (user client)
│  (telethon)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Filtering   │  ← Spam, dedup, short messages
│  (rules.py)  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Categorization  │  ← Rule-based → AI fallback
│  (hybrid)        │
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│  Scoring     │  ← Heuristic importance (0–10)
│  (scorer.py) │
└──────┬──────┘
       │
       ▼
┌──────────────┐
│  Selection    │  ← Adaptive threshold (5–15 items)
│  (selector)   │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  AI Intelligence  │  ← Only for selected items
│  (OpenRouter)     │
└──────┬───────────┘
       │
       ▼
┌─────────────┐
│  Report Gen  │  ← HTML + Text output
│  (Jinja2)    │
└─────────────┘
```

---

## 📦 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-username/Tsync.git
cd Tsync
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API credentials
```

Get your credentials:
- **Telegram**: [my.telegram.org](https://my.telegram.org) → API Development Tools
- **OpenRouter**: [openrouter.ai](https://openrouter.ai) → API Keys

### 3. Add Channels

```bash
python main.py --add-channel techcrunch
python main.py --add-channel finance_news
python main.py --channels  # List all
```

### 4. Run

```bash
# Full pipeline (Telegram + Processing)
python main.py

# Demo mode (sample data, no Telegram needed)
python main.py --demo

# Process-only mode (skip ingestion)
python main.py --process
```

---

## 🖥️ Demo Mode

Run without Telegram credentials to see the system in action:

```bash
python main.py --demo
```

This inserts 15 realistic sample messages and runs the full pipeline, generating both HTML and text reports.

---

## 📂 Project Structure

```
Tsync/
├── main.py              # Pipeline orchestrator + CLI
├── telegram_client.py   # Telethon-based message collector
├── ai_processor.py      # OpenRouter AI fallback processor
├── rules.py             # Rule-based categorization engine
├── scorer.py            # Heuristic importance scorer
├── selector.py          # Dynamic message selector
├── trends.py            # Trend detection & analysis
├── database.py          # SQLite storage layer
├── report.py            # HTML/Text report generator
├── templates/
│   ├── report.html      # Jinja2 HTML template
│   └── styles.css       # Dark theme stylesheet
├── config.json          # Channel & pipeline config
├── .env.example         # Environment variables template
├── requirements.txt     # Python dependencies
├── .github/
│   └── workflows/
│       └── daily_report.yml  # Automated daily execution
└── README.md
```

---

## ⚙️ Configuration

### config.json

| Field | Description | Default |
|---|---|---|
| `channels` | Telegram channel usernames | `[]` |
| `message_limit` | Max messages per channel | `100` |
| `importance_threshold` | Base score threshold | `7` |
| `min_items` | Minimum selected items | `5` |
| `max_items` | Maximum selected items | `15` |
| `min_message_length` | Skip messages shorter than | `30` |

### .env

| Variable | Description |
|---|---|
| `TELEGRAM_API_ID` | Telegram API ID |
| `TELEGRAM_API_HASH` | Telegram API Hash |
| `OPENROUTER_API_KEY` | OpenRouter API Key |

---

## 📊 Intelligence Output

Each selected item includes:

| Field | Description |
|---|---|
| **Headline** | Concise, impactful title |
| **What** | Factual summary (2–3 sentences) |
| **Why It Matters** | Impact and implications |
| **Category** | technology, finance, geopolitics, etc. |
| **Score** | Importance rating (0–10) |
| **Source** | Telegram channel |

---

## 🔄 CLI Reference

```bash
python main.py                          # Full pipeline
python main.py --demo                   # Demo with sample data
python main.py --process                # Process without ingestion
python main.py --channels               # List channels
python main.py --add-channel <name>     # Add channel
python main.py --remove-channel <name>  # Remove channel
python main.py --help                   # Show help
```

---

## 🤖 GitHub Actions

The included workflow runs daily at 06:00 UTC:

1. Set repository secrets: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `OPENROUTER_API_KEY`
2. Reports are committed to `reports/` directory
3. Also available as downloadable artifacts

Trigger manually via **Actions → Tsync Daily Intelligence Report → Run workflow**.

---

## 📄 License

MIT License
