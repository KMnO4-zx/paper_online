<div align='center'>
    <img src="./images/head.png" alt="alt text" width="90%">
    <h1><a href="https://paper-online.onrender.com">Paper Insight</a></h1>
</div>

## 🎯 项目介绍

*&emsp;&emsp;做这个工具的起因是，老板说要看足够多的论文才会有很好的 idea 或 insight ，我觉得很对。（感谢王老师的读论文 Prompt）所以用 dify 联合飞书做了工作流，但是每次只手动输入能看一篇；后来做了好几个仓库用于批量拉取AI会议的论文，这样我可以直接看然后跳转到 dify 工作流；再然后我觉得 dify 太慢了，于是 vibe 了一个更快的工具 paper insight，直接在本地就能快速分析论文，看看摘要、关键词、相关工作推荐等，觉得有潜力就收藏到zotero里精读；我又觉得每次新的会议出来我就得新搞一个仓库太麻烦了，于是写了一个通用的爬虫脚本，能批量导入会议论文；最后我觉得如果能直接在这个工具里浏览会议论文就更好了，于是又加了一个会议浏览的功能，支持分页和关键词搜索。so，果然省事才是第一生产力。如果你喜欢这个项目，欢迎点个star哦~*

&emsp;&emsp;Paper Insight 是一个基于 FastAPI 和 Supabase 的在线论文分析工具，利用 LLM 技术为用户提供论文摘要、关键词提取、相关工作推荐等功能，帮助研究人员快速理解和分析学术论文。

&emsp;&emsp;本项目旨在辅助快速浏览 AI 会议论文。通过 AI 快速生成摘要，用户可决定是否将论文收藏至 Zotero 进行精读。目前仅支持 OpenReview 平台上的论文，作为作者个人论文阅读工作流的一部分，暂无计划支持其他平台。

***&emsp;&emsp;可访问  https://paper-online.onrender.com 在线体验，或按照以下步骤在本地部署。***

&emsp;&emsp;已支持：[ICLR 2026](https://github.com/KMnO4-zx/iclr26-all-papers), [NeurIPS 2025](https://kmno4-zx.github.io/nips25-all-papers/)。

> *注：LLM 使用 OpenRouter 接入 Step-3.5-Flash(Free) 模型，因为其免费且性能较好，适合当前的论文分析需求。后续将支持更多会议论文，并统一格式。*

### 🤔 为什么不用 [cool papers](https://papers.cool/)？

&emsp;&emsp;cool papers 是苏神开发的优秀论文阅读工具，但两者的设计理念不同：

| 对比维度 | Paper Insight | cool papers |
|---------|--------------|-------------|
| **定位** | 快速筛选论文 | 深度理解论文 |
| **分析问题数** | 4 个核心问题 | 6 个详细问题 |
| **核心问题** | • 代码开源吗？<br>• 解决什么任务？<br>• 用什么评估指标？<br>• 为什么比 Baseline 好？ | • 试图解决什么问题？<br>• 有哪些相关研究？<br>• 如何解决这个问题？<br>• 做了哪些实验？<br>• 可进一步探索的点？<br>• 总结主要内容 |
| **适用场景** | 第一时间判断论文价值，决定是否精读 | 全面理解论文细节和研究脉络 |
| **额外功能** | • 会议论文批量浏览<br>• 字段过滤搜索<br>• 论文对话 | • 详细的论文解读<br>• 完整的研究背景 |

&emsp;&emsp;**简而言之**：Paper Insight 专注于"快速筛选"，帮你在海量论文中找到值得精读的那几篇；cool papers 专注于"深度理解"，帮你全面掌握一篇论文的方方面面。两者互补，可根据需求选择。

## ✨ 功能特性

### 📄 论文分析
- **快速分析**：输入 OpenReview 论文 ID，AI 自动生成论文摘要、关键词和相关工作推荐
- **智能缓存**：分析结果自动保存到数据库，再次访问秒开
- **重新分析**：支持重新生成分析结果
- **流式输出**：实时显示 AI 分析过程，无需等待

### 🗂️ 会议浏览
- **批量浏览**：支持 NeurIPS 2025、ICLR 2026 等会议的所有论文
- **分页展示**：每页 8 篇论文，支持页面跳转
- **字段过滤搜索**：可选择在标题、摘要、关键词中搜索，精准定位目标论文
- **快捷键**：Shift+Enter 快速搜索
- **智能缓存**：24小时缓存，二次访问秒开

### 💬 论文对话
- **智能问答**：基于论文内容进行多轮对话
- **上下文记忆**：保持对话上下文，理解连续提问
- **历史会话**：自动保存对话历史，随时查看
- **重新生成**：支持重新生成最后一条回复

### 🔧 其他功能
- **在线人数**：实时显示当前在线用户数
- **批量导入**：支持从 JSONL 文件批量导入会议论文
- **响应式设计**：支持桌面和移动端访问

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

**方式三：浏览会议论文**

访问会议论文列表页面：
- NeurIPS 2025: `http://localhost:8000/?conference=neurips_2025`
- ICLR 2026: `http://localhost:8000/?conference=iclr_2026`

支持关键词搜索（标题、摘要、关键词），使用 Shift+Enter 快捷键搜索。

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
│   ├── index.html      # 主页面
│   ├── css/
│   │   └── style.css   # 样式文件
│   └── js/
│       ├── api.js      # API 客户端
│       ├── home.js     # 主页逻辑
│       ├── paper.js    # 论文展示
│       ├── chat.js     # 对话功能
│       ├── conference.js  # 会议浏览
│       ├── online.js   # 在线人数
│       ├── main.js     # 路由初始化
│       └── utils.js    # 工具函数
├── scripts/
│   ├── import_papers.py  # 批量导入论文
│   └── migrate_db.sql    # 数据库迁移
└── crawled_data/         # 爬虫数据存储
    ├── neurips_2025/
    └── iclr_2026/
```

## 📦 批量导入论文

如果你有会议论文的 JSONL 数据文件，可以使用以下命令批量导入：

```bash
python scripts/import_papers.py --conference neurips_2025
python scripts/import_papers.py --conference iclr_2026
```

数据文件应放在 `crawled_data/{conference}/` 目录下。

## License

Apache 2.0 License
