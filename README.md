<div align='center'>
    <img src="./images/head.png" alt="alt text" width="100%">
    <h1><a href="https://paper-online.onrender.com">Paper Insight</a></h1>
</div>

## 🎯 项目介绍

&emsp;&emsp;Paper Insight 是一个基于 FastAPI 和 Supabase 的在线论文分析工具，利用 LLM 技术为用户提供论文摘要、关键词提取、相关工作推荐等功能，帮助研究人员快速理解和分析学术论文。

&emsp;&emsp;本项目旨在辅助快速浏览 AI 会议论文。通过 AI 快速生成摘要，用户可决定是否将论文收藏至 Zotero 进行精读。目前仅支持 OpenReview 平台上的论文，作为作者个人论文阅读工作流的一部分，暂无计划支持其他平台。

&emsp;&emsp;已支持：[ICLR 2026](https://github.com/KMnO4-zx/iclr26-all-papers), [NeurIPS 2025](https://kmno4-zx.github.io/nips25-all-papers/)。

> *注：LLM 使用 OpenRouter 接入 Step-3.5-Flash(Free) 模型，因为其免费且性能较好，适合当前的论文分析需求。后续将支持更多会议论文，并统一格式。*

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

在项目根目录下创建 `.env` 文件，并填入以下内容：

```bash
SILICONFLOW_API_KEY=your_api_key_here
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY=your_supabase_key
```

### 3. 启动服务

```bash
cd backend
uv run uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### 4. 访问页面

服务启动后，打开浏览器访问以下地址：

**方式一：主页访问**

访问 `http://localhost:8000/`，在输入框中填入 OpenReview 论文 ID，点击"分析"。

**方式二：通过 URL 参数访问**

直接访问带 ID 的链接，例如：`http://localhost:8000/?id=uq6UWRgzMr`

## 停止服务

在终端按 `Ctrl + C` 停止服务。

## 生产部署

### 本地部署

运行以下命令启动服务：

```bash
cd backend
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

### Render 部署

1. 将 GitHub 仓库连接到 Render。
2. 选择 Docker 环境进行构建。
3. 在 Environment 中配置环境变量：
   - `SILICONFLOW_API_KEY`
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY`

## 项目结构

```
paper_online/
├── backend/
│   ├── app.py          # FastAPI 主应用
│   ├── chat.py         # 聊天会话管理
│   ├── database.py     # Supabase 数据库操作
│   ├── llm.py          # LLM 调用封装
│   ├── prompt.py       # 系统提示词
│   └── utils.py        # 工具函数
├── frontend/
│   └── index.html      # 前端页面
└── README.md
```

## License

Apache 2.0 License
