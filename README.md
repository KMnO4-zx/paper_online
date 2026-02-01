# Paper Insight

AI 驱动的学术论文智能分析工具，基于 FastAPI + SSE 流式输出。

## 功能特性

- 自动获取 OpenReview 论文信息
- 通过 Jina Reader 解析 PDF 内容
- LLM 流式分析论文（打字机效果）
- SQLite 本地缓存，避免重复请求
- 支持 Markdown 和数学公式渲染
- 自动适配系统深色/浅色模式

## 环境要求

- Python >= 3.12
- uv 包管理器

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
SILICONFLOW_API_KEY=your_api_key_here
```

### 3. 启动服务

```bash
cd backend
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问页面

打开浏览器访问：

```
http://localhost:8000/?id=论文ID
```

例如：`http://localhost:8000/?id=uq6UWRgzMr`

## 停止服务

在终端按 `Ctrl + C` 即可停止服务。

## 生产部署

```bash
cd backend
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

## 项目结构

```
paper_online/
├── backend/
│   ├── app.py          # FastAPI 主应用
│   ├── llm.py          # LLM 调用封装
│   ├── utils.py        # 工具函数
│   ├── database.py     # SQLite 数据库
│   └── prompt.py       # 系统提示词
├── frontend/
│   └── index.html      # 前端页面
└── README.md
```

## License

MIT
