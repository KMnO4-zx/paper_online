# ChangeLog History

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

