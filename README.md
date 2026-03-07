<div align='center'>

<img src="./images/head.png" alt="alt text" width="90%">
<h1><a href="https://paper-online.onrender.com">Paper Insight</a></h1>

English | [简体中文](./README_zh.md)

</div>

## 🎯 Project Introduction

&emsp;&emsp;Paper Insight is an online paper analysis tool built with FastAPI and Supabase, leveraging LLM technology to provide paper summaries, keyword extraction, and related work recommendations, helping researchers quickly understand and analyze academic papers.

&emsp;&emsp;This project aims to assist in quickly browsing AI conference papers. Through AI-generated summaries, users can decide whether to save papers to Zotero for in-depth reading. Currently supports papers from the OpenReview platform only, as part of the author's personal paper reading workflow, with no plans to support other platforms.

***&emsp;&emsp;Visit https://paper-online.onrender.com for online experience, or follow the steps below for local deployment.***

&emsp;&emsp;Supported conferences: [ICLR 2026](https://paper-online.onrender.com/?conference=iclr_2026), [NeurIPS 2025](https://paper-online.onrender.com/?conference=neurips_2025), [ICML 2025](https://paper-online.onrender.com/?conference=icml_2025)

> *Note: Uses OpenRouter to access Step-3.5-Flash (Free) model for its free tier and good performance, suitable for current paper analysis needs. More conferences will be supported with unified format.*

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
- **Quick Analysis**: Input OpenReview paper ID, AI automatically generates paper summary, keywords, and related work recommendations
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

```bash
uv sync
```

### 2. Configure Environment Variables

Create a `.env` file in the project root directory with the following content:

```bash
SILICONFLOW_API_KEY=your_api_key_here
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY=your_supabase_key
```

### 3. Start Service

```bash
cd backend
uv run uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### 4. Access the Application

After the service starts, open your browser and visit:

**Method 1: Homepage Access**

Visit `http://localhost:8000/`, enter an OpenReview paper ID in the input box, and click "Analyze".

**Method 2: Direct URL Access**

Directly visit a link with ID, for example: `http://localhost:8000/?id=uq6UWRgzMr`

**Method 3: Browse Conference Papers**

Visit conference paper list pages:
- NeurIPS 2025: `http://localhost:8000/?conference=neurips_2025`
- ICLR 2026: `http://localhost:8000/?conference=iclr_2026`

Supports keyword search (title, abstract, keywords), use Shift+Enter shortcut for search.

## Stop Service

Press `Ctrl + C` in the terminal to stop the service.

## Production Deployment

### Local Deployment

Run the following command to start the service:

```bash
cd backend
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

### Render Deployment

1. Connect your GitHub repository to Render.
2. Select Docker environment for build.
3. Configure environment variables in Environment:
   - `SILICONFLOW_API_KEY`
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY`

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
├── frontend/
│   ├── index.html      # Main page
│   ├── css/
│   │   └── style.css   # Stylesheet
│   └── js/
│       ├── api.js      # API client
│       ├── home.js     # Homepage logic
│       ├── paper.js    # Paper display
│       ├── chat.js     # Chat functionality
│       ├── conference.js  # Conference browsing
│       ├── online.js   # Online user count
│       ├── main.js     # Route initialization
│       └── utils.js    # Utility functions
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
```

Data files should be placed in the `crawled_data/{conference}/` directory.

## License

Apache 2.0 License
