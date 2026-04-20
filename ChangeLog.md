# ChangeLog History

## 2026-04-20

- 🔐 新增正式账号系统：支持邮箱密码注册 / 登录、HTTP-only Cookie 会话、密码修改、退出登录，并将论文聊天历史绑定到登录账号。
- ⭐ 将论文“看过 / 点赞”改为数据库持久化：新增 `paper_marks`，记录 `viewed_at`、`liked_at`、`updated_at`，为后续推荐系统提供用户行为数据基础。
- 👤 新增个人主页 `/me`：展示用户看过和点赞过的论文，支持按最近看过、最近点赞、收藏优先、最近操作、标题排序，并支持筛选全部 / 看过 / 已点赞。
- 🛠️ 新增管理员后台 `/admin`：展示当前在线人数、登录用户 / 游客拆分、历史在线趋势，并支持用户启停、重置密码和修改管理员密码。
- 📈 将在线人数从进程内状态迁移到 PostgreSQL：新增 `presence_heartbeats` 和 `presence_snapshots`，后端定期写入在线趋势快照。
- ⚙️ 统一运行时配置到 `config.yaml`：新增 `backend/config.py`、`config.yaml.example` 和 Docker Compose 启动辅助脚本，移除运行时 `.env.example` 主路径。
- 🚀 改进启动流程：后端启动时自动执行 SQL migration，并在缺少有效 LLM key 时跳过后台分析，避免启动后因缺表或错误 key 持续报错。
- 🧭 调整论文卡片交互：列表页不再展示 OpenReview / PDF 按钮，保留详情页 PDF 和 KIMI 入口；看过 / 点赞按钮移动到卡片左侧。
- 🧯 优化未登录状态：未登录访问论文 marks 和聊天 session 列表时静默返回空数据，避免前端正常浏览时刷 `401 Unauthorized` 日志。
- 📚 更新中英文 README：补充账号系统、个人论文库、管理员后台、`config.yaml` 配置方式和最新本地 / Docker 启动说明。

## 2026-04-17

- 🐘 完成数据库解耦：移除运行时对 Supabase SDK 的依赖，后端改为基于 `psycopg` 直连 PostgreSQL，自托管 PostgreSQL 16 成为新的主路径。
- 🧱 新增完整数据库初始化能力：补齐 `db/migrations/`、`scripts/apply_migrations.py`、`db/seeds/dev_seed.sql`、单文件 `scripts/migrate_db.sql`，支持空库初始化、开发 seed 和结构化迁移。
- 🐳 增加单机 VPS 部署基础设施：引入 `docker-compose.yml` 和 `config.yaml.example`，并让应用容器启动前自动执行 migration。
- 📦 调整数据导入流程：`scripts/import_papers.py` 改为直连 PostgreSQL，继续支持从 `crawled_data/{conference}` 批量导入 ICLR 2026、NeurIPS 2025、ICML 2025。
- 🗃️ 新增论文正文磁盘缓存：Jina Reader 返回的正文不再重复远程抓取，而是按 `paper_id` 缓存到 `data/paper_cache/`，analysis / chat / 后台分析统一复用本地缓存。
- 🔐 收紧 Docker 部署默认值：`POSTGRES_PASSWORD` 改为必须显式提供，不再允许 `change-me` 弱默认值；同时为 `/app/data` 增加命名 volume，持久化 `paper_cache`。
- 🧭 增加论文详情页外链能力：在论文详情页新增 `Open in KIMI` 按钮，自动携带面向论文讲解的预填 prompt、PDF 链接以及 `send_immediately=true`。
- 📚 更新中英文 README 与开发说明：补充本地 PostgreSQL 启停、开发者指南、缓存目录说明、自托管部署路径，并移除普通开发者不需要的 Supabase 导出主流程。

## 2026-03-18

- 🧹 移除旧 `frontend/` 静态前端依赖，FastAPI 不再回退托管旧版 HTML/CSS/JS。
- 🚦 收紧前端入口策略：仅保留 React SPA 路由，旧参数式 URL 不再自动兼容跳转。
- ⚠️ 明确未构建前端时的行为：若 `frontend-react/dist` 缺失，后端会返回清晰错误并提示先执行前端构建。
- 📚 同步更新中英文 README 与 AGENTS，移除“legacy frontend fallback”相关说明。

## 2026-03-16

- ⚛️ 新建 `frontend-react`，基于 React 重写前端并接入现有 FastAPI 后端，覆盖首页、会议页、全局搜索、论文详情、AI 分析流式输出、论文聊天、历史会话与在线人数。
- 🧭 完成前后端路由整合：生产环境下由 FastAPI 直接托管 React 构建产物，支持 `/`、`/search`、`/conference/:venue`、`/papers/:id` 等 SPA 路由入口。
- 💬 优化论文详情页交互：修复 AI 分析重复显示、聊天流式回复导致整页跳顶、历史对话默认展开等问题，并调整聊天栏吸顶、宽度、高度与滚动行为。
- 🎨 调整前端视觉细节：统一使用原始 `images/logo.svg`，新增小红书入口，优化导航栏与按钮交互；同时放宽论文详情页容器、调整卡片底色、隐藏作者信息、增大正文与标签样式。
- 🔍 统一搜索交互：首页、会议页和全局搜索页均改为仅支持“点击搜索按钮”或 `Shift+Enter` 触发搜索，禁用普通 `Enter` 提交。
- 🛡️ 提升后端稳定性：修复 PDF 文本包含 `<|endoftext|>` 时的分词报错，为 Supabase 关键查询增加重试与错误兜底，避免数据库瞬断直接导致接口或 SSE 崩溃。
- 📚 更新工程文档与部署说明：补充 `frontend-react` 的开发/生产运行方式，更新中英文 README 的 Docker 与 Render 部署文档，并完善 `.gitignore` 对前端构建产物和依赖目录的忽略。

## 2026-03-15

- 🚀 完成数据库搜索优化第一阶段：将会议搜索和全局搜索下推到 Supabase RPC，避免 Python 侧全量拉取、内存排序和 `id.in()` URL 过长问题。
- 🔎 完成数据库搜索优化第二阶段：将 `ILIKE` 搜索升级为 PostgreSQL Full Text Search，使用 `english` 词典，并按相关性优先排序搜索结果。
- ⚡ 为 `papers.title`、`papers.abstract` 和 `keywords.keyword` 新增 GIN 索引，加速全文检索。
- 🧱 优化写入性能：`save_paper()` 改为批量写入 authors 和 keywords，减少 Supabase 往返请求。
- 📦 优化导入脚本：`scripts/import_papers.py` 改为按批次批量删除并写入 authors 和 keywords，提升批量导入效率。
- 🛡️ 修复超长论文上下文问题：在发送给 LLM 前使用 `tiktoken` 按 token 截断正文，避免超出模型上下文上限。
