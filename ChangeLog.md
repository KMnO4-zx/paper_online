# ChangeLog History

## 2026-03-15

- 完成数据库搜索优化第一阶段：将会议搜索和全局搜索下推到 Supabase RPC，避免 Python 侧全量拉取、内存排序和 `id.in()` URL 过长问题。
- 完成数据库搜索优化第二阶段：将 `ILIKE` 搜索升级为 PostgreSQL Full Text Search，使用 `english` 词典，并按相关性优先排序搜索结果。
- 为 `papers.title`、`papers.abstract` 和 `keywords.keyword` 新增 GIN 索引，加速全文检索。
- 优化写入性能：`save_paper()` 改为批量写入 authors 和 keywords，减少 Supabase 往返请求。
- 优化导入脚本：`scripts/import_papers.py` 改为按批次批量删除并写入 authors 和 keywords，提升批量导入效率。
