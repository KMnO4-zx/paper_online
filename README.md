<div align='center'>

<img src="./images/head.png" alt="alt text" width="90%">
<h1><a href="https://paper-online.onrender.com">Paper Insight</a></h1>

English | [简体中文](./README_zh.md)

</div>

## 🎯 Project Introduction

&emsp;&emsp;Paper Insight is an online paper analysis tool built with FastAPI and PostgreSQL, leveraging LLM technology to provide fast paper analysis and interactive chat, helping researchers quickly understand and screen academic papers.

&emsp;&emsp;This project aims to assist in quickly browsing AI conference papers. Through AI-generated summaries, users can decide whether to save papers to Zotero for in-depth reading. Currently supports papers from the OpenReview platform only, as part of the author's personal paper reading workflow, with no plans to support other platforms.

***&emsp;&emsp;Visit https://paper-online.onrender.com for online experience, or follow the steps below for local deployment.***

&emsp;&emsp;Supported conferences: [ICLR 2026](https://paper-online.onrender.com/conference/iclr_2026), [NeurIPS 2025](https://paper-online.onrender.com/conference/neurips_2025), [ICML 2025](https://paper-online.onrender.com/conference/icml_2025)

> *Note: The default LLM provider is OpenRouter, currently using `stepfun/step-3.5-flash:free`. More conferences will be supported with unified format.*

### 🤔 Why not [cool papers](https://papers.cool/)?

&emsp;&emsp;cool papers is an excellent paper reading tool developed by Su Jianlin, but the two tools have different design philosophies:

| Dimension | Paper Insight | cool papers |
|---------|--------------|-------------|
| **Positioning** | Quick paper screening | Deep paper understanding |
| **Analysis Questions** | 4 core questions | 6 detailed questions |
| **Core Questions** | • Is code open-sourced?<br>• What task does it solve?<br>• What evaluation metrics?<br>• Why better than baseline? | • What problem to solve?<br>• Related research?<br>• How to solve it?<br>• What experiments?<br>• Further exploration?<br>• Summary |
| **Use Case** | Quickly judge paper value, decide whether to read in-depth | Comprehensively understand paper details and research context |
| **Extra Features** | • Conference paper browsing<br>• Field-filtered search<br>• Paper chat | • Detailed paper interpretation<br>• Complete research background |

&emsp;&emsp;**In short**: Paper Insight focuses on "quick screening" to help you find papers worth reading in-depth from a large volume; cool papers focuses on "deep understanding" to help you comprehensively grasp all aspects of a paper. They complement each other—choose based on your needs.

## ✨ Features

### 📄 Paper Analysis
- **Quick Analysis**: Input an OpenReview paper ID, and AI answers four core questions: whether code is available, what task the paper solves, what metrics it uses, and why the method improves over baseline
- **Smart Caching**: Analysis results automatically saved to database, instant access on revisit
- **Re-analysis**: Support regenerating analysis results
- **Streaming Output**: Real-time display of AI analysis process, no waiting

### 🗂️ Conference Browsing
- **Batch Browsing**: Support all papers from NeurIPS 2025, ICLR 2026, and other conferences
- **Paginated Display**: 8 papers per page, support page jumping
- **Field-Filtered Search**: Search in title, abstract, or keywords to precisely locate target papers
- **Keyboard Shortcut**: Shift+Enter for quick search
- **Smart Caching**: 24-hour cache, instant access on revisit

### 💬 Paper Chat
- **Intelligent Q&A**: Multi-turn conversation based on paper content
- **Context Memory**: Maintain conversation context, understand continuous questions
- **Chat History**: Automatically save chat history, view anytime
- **Regenerate**: Support regenerating the last reply

### 🔧 Other Features
- **Online Users**: Real-time display of current online user count
- **Batch Import**: Support batch importing conference papers from JSONL files
- **Responsive Design**: Support desktop and mobile access

## Quick Start

### 1. Install Dependencies

Backend dependencies:

```bash
uv sync
```

Frontend dependencies:

```bash
cd frontend-react
npm install
```

### 2. Prepare Local PostgreSQL 16

Using Homebrew on macOS:

```bash
brew install postgresql@16
brew services start postgresql@16
createdb paper_online
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend/` directory with the following content:

```bash
DATABASE_URL=postgresql:///paper_online
OPEN_ROUTER_API_KEY=your_api_key_here
```

If you want to switch providers manually, you can also configure optional keys such as `SILICONFLOW_API_KEY`, but the current default runtime uses `OPEN_ROUTER_API_KEY`.

Initialize the database schema:

```bash
uv run python scripts/apply_migrations.py
```

For a minimal local dataset:

```bash
uv run python scripts/apply_migrations.py --seed dev
```

### 4. Start in Development Mode

Start the backend:

```bash
cd backend
uv run uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Start the React frontend in another terminal:

```bash
cd frontend-react
npm run dev
```

### 5. Access the Application

Development mode:
- Frontend: `http://127.0.0.1:5173`
- Backend API: `http://127.0.0.1:8000`

Recommended routes:
- Home: `http://127.0.0.1:5173/`
- Global search: `http://127.0.0.1:5173/search?q=agent`
- Conference page: `http://127.0.0.1:5173/conference/iclr_2026`
- Paper detail: `http://127.0.0.1:5173/papers/uq6UWRgzMr`

Search is triggered by clicking the search button or pressing `Shift+Enter`.
Legacy query-style URLs such as `/?id=...`, `/?conference=...`, and `/?search=...` are no longer supported.

## Stop Service

Press `Ctrl + C` in each terminal to stop the backend and frontend dev servers.

## 👩‍💻 Developer Guide

This section focuses on the three common local-development tasks:

1. Start / stop local PostgreSQL
2. Prepare the local development database
3. Prepare local development data

### 1. Start / stop local PostgreSQL

If you installed `postgresql@16` with Homebrew on macOS, these are the commands you will use most often:

```bash
# Start
brew services start postgresql@16

# Stop
brew services stop postgresql@16

# Restart
brew services restart postgresql@16

# Check status
brew services list | grep postgresql@16
```

You can also run PostgreSQL manually in the foreground, but for this repo `brew services` is the simplest path.

### 2. Prepare the local development database

Use `paper_online` as the default local database name:

```bash
# Run once
createdb paper_online

# Initialize tables, indexes, and search functions
DATABASE_URL=postgresql:///paper_online uv run python scripts/apply_migrations.py
```

If you want to reset everything:

```bash
dropdb --if-exists paper_online
createdb paper_online
DATABASE_URL=postgresql:///paper_online uv run python scripts/apply_migrations.py
```

### 3. Two ways to prepare local data

#### Option A: minimal dev seed

Good for booting the UI quickly and validating APIs without full production data.

```bash
DATABASE_URL=postgresql:///paper_online uv run python scripts/apply_migrations.py --seed dev
```

#### Option B: rebuild from `crawled_data/`

Use this if you do not want to depend on the online dump, or if you want to rebuild / add conference data from crawler output.

First initialize the database:

```bash
DATABASE_URL=postgresql:///paper_online uv run python scripts/apply_migrations.py
```

Then import by conference:

```bash
uv run python scripts/import_papers.py --conference neurips_2025
uv run python scripts/import_papers.py --conference iclr_2026
uv run python scripts/import_papers.py --conference icml_2025
```

Notes:

- Source directory is always `crawled_data/{conference}/`
- Import is overwrite-style per paper
- `papers` uses upsert
- `authors` and `keywords` are deleted then re-inserted for touched papers
- `llm_response` is not generated during import; it is filled later by user-triggered analysis or the background analyzer

### 4. Paper content disk cache

The paper body returned by Jina Reader is **not stored in PostgreSQL**. It is cached on disk under:

```text
data/paper_cache/
```

Current behavior:

- The first paper analysis fetches the PDF text from Jina Reader if the cache is missing
- The first chat-session initialization also fetches it if the cache is missing
- Once cached, analysis / chat / background analysis reuse the local text file

To force a fresh fetch, delete the cache directory:

```bash
rm -rf data/paper_cache
```

### 5. Recommended local dev flow

For a new contributor, this is the shortest path:

```bash
brew services start postgresql@16
createdb paper_online
cp backend/.env.example backend/.env
# edit backend/.env and fill OPEN_ROUTER_API_KEY
DATABASE_URL=postgresql:///paper_online uv run python scripts/apply_migrations.py --seed dev
cd backend && uv run uvicorn app:app --reload --host 127.0.0.1 --port 8000
cd frontend-react && npm run dev
```

## Deployment

### Deployment Modes

There are now two modes:

1. Development mode
   - Run FastAPI and `frontend-react` separately.
   - Use this for local development and UI debugging.

2. Production mode
   - Build `frontend-react` into static assets.
   - FastAPI serves the built React app directly.
   - Only one service needs to run in production.

### Local Production Run

Build the frontend:

```bash
cd frontend-react
npm run build
```

Then start FastAPI:

```bash
cd backend
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

If `frontend-react/dist` does not exist, FastAPI now returns a clear error telling you to build the frontend first. There is no legacy static frontend fallback anymore.

### Docker / VPS Deployment

This repository includes a production-ready [Dockerfile](./Dockerfile).
It builds `frontend-react`, copies `frontend-react/dist` into the final image, applies PostgreSQL migrations on startup, and launches FastAPI.

For VPS deployment, prefer `docker compose`:

```bash
cp .env.example .env
# Fill in POSTGRES_PASSWORD, OPEN_ROUTER_API_KEY, and any optional LLM keys.
docker compose up --build -d
```

If you only need the application image:

```bash
docker build -t paper-insight .
```

At runtime, the app expects a valid `DATABASE_URL`. On VPS, the included `docker-compose.yml` wires the app to a PostgreSQL 16 container automatically.

## Project Structure

```
paper_online/
├── backend/
│   ├── app.py          # FastAPI main application
│   ├── chat.py         # Chat session management
│   ├── database.py     # PostgreSQL database operations
│   ├── llm.py          # LLM API wrapper
│   ├── prompt.py       # System prompts
│   └── utils.py        # Utility functions
├── db/
│   ├── migrations/     # PostgreSQL schema and search functions
│   └── seeds/          # Minimal local development dataset
├── frontend-react/
│   ├── src/            # React frontend source code
│   ├── dist/           # Built frontend assets
│   └── vite.config.ts  # Vite config
├── scripts/
│   ├── apply_migrations.py # Apply migrations / optional seed
│   ├── import_papers.py    # Batch import papers
│   └── migrate_db.sql      # Single-file database migration
└── crawled_data/         # Crawler data storage
    ├── neurips_2025/
    └── iclr_2026/
```

## 📦 Batch Import Papers

If you have JSONL data files of conference papers, you can batch import them using:

```bash
uv run python scripts/import_papers.py --conference neurips_2025
uv run python scripts/import_papers.py --conference iclr_2026
uv run python scripts/import_papers.py --conference icml_2025
```

Data files should be placed in the `crawled_data/{conference}/` directory.

## License

Apache 2.0 License
