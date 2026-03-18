<div align='center'>

<img src="./images/head.png" alt="alt text" width="90%">
<h1><a href="https://paper-online.onrender.com">Paper Insight</a></h1>

English | [简体中文](./README_zh.md)

</div>

## 🎯 Project Introduction

&emsp;&emsp;Paper Insight is an online paper analysis tool built with FastAPI and Supabase, leveraging LLM technology to provide fast paper analysis and interactive chat, helping researchers quickly understand and screen academic papers.

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

### 2. Configure Environment Variables

Create a `.env` file in the `backend/` directory with the following content:

```bash
OPEN_ROUTER_API_KEY=your_api_key_here
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY=your_supabase_key
```

If you want to switch providers manually, you can also configure optional keys such as `SILICONFLOW_API_KEY`, but the current default runtime uses `OPEN_ROUTER_API_KEY`.

### 3. Start in Development Mode

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

### 4. Access the Application

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

### Docker Deployment

This repository includes a production-ready [Dockerfile](./Dockerfile).
It builds `frontend-react`, copies `frontend-react/dist` into the final image, and starts FastAPI only.

Build the image:

```bash
docker build -t paper-insight .
```

Run the container:

```bash
docker run -p 8000:8000 \
  -e OPEN_ROUTER_API_KEY=your_api_key_here \
  -e NEXT_PUBLIC_SUPABASE_URL=your_supabase_url \
  -e NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY=your_supabase_key \
  paper-insight
```

### Render Deployment

Yes, the current repository can be deployed to Render directly using Docker.

Recommended setup:
1. Connect the GitHub repository to Render.
2. Create a new `Web Service`.
3. Choose `Docker` as the runtime.
4. Use the repository root as the service root.
5. Configure environment variables:
   - `OPEN_ROUTER_API_KEY`
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY`
6. Deploy.

Notes:
- Render will use the existing [Dockerfile](./Dockerfile); no separate frontend service is needed.
- The React frontend is served by FastAPI in production.
- On Render free instances, sleeping is still a product constraint. Background tasks do not prevent the instance from sleeping.

## Project Structure

```
paper_online/
├── backend/
│   ├── app.py          # FastAPI main application
│   ├── chat.py         # Chat session management
│   ├── database.py     # Supabase database operations
│   ├── llm.py          # LLM API wrapper
│   ├── prompt.py       # System prompts
│   └── utils.py        # Utility functions
├── frontend-react/
│   ├── src/            # React frontend source code
│   ├── dist/           # Built frontend assets
│   └── vite.config.ts  # Vite config
├── scripts/
│   ├── import_papers.py  # Batch import papers
│   └── migrate_db.sql    # Database migration
└── crawled_data/         # Crawler data storage
    ├── neurips_2025/
    └── iclr_2026/
```

## 📦 Batch Import Papers

If you have JSONL data files of conference papers, you can batch import them using:

```bash
python scripts/import_papers.py --conference neurips_2025
python scripts/import_papers.py --conference iclr_2026
python scripts/import_papers.py --conference icml_2025
```

Data files should be placed in the `crawled_data/{conference}/` directory.

## License

Apache 2.0 License
