# 数据库重构实现

## 概述

本目录包含数据库迁移和数据导入的脚本。

## 文件说明

- `migrate_db.sql` - SQL 迁移脚本，用于创建新表和修改现有表结构
- `import_papers.py` - Python 脚本，用于将 JSONL 文件中的论文数据导入 Supabase

## 数据库迁移步骤

### 1. 执行 SQL 迁移

在 Supabase SQL Editor 中执行 `migrate_db.sql`，完成以下操作：
- 创建 `authors` 表
- 创建 `keywords` 表
- 为 `papers` 表添加 `venue` 和 `primary_area` 列
- 创建 `search_papers_optimized` 和 `count_papers_optimized` RPC 函数

### 1.1 第一阶段搜索优化部署顺序

第一阶段数据库优化依赖 Supabase RPC 函数。推荐部署顺序：

1. 先在 Supabase SQL Editor 执行最新的 `migrate_db.sql`
2. 确认 `search_papers_optimized` 和 `count_papers_optimized` 已创建成功
3. 再部署后端代码

如果先部署了后端代码但 Supabase 尚未执行 RPC SQL，系统会自动回退到旧的 Python 搜索逻辑，功能不会中断，但不会获得新的性能优化收益。

### 1.2 第二阶段 FTS 升级说明

第二阶段会继续复用同名 RPC：

- `search_papers_optimized`
- `count_papers_optimized`

但其内部实现会从 `ILIKE` 升级为 PostgreSQL Full Text Search，使用 `english` 词典，并新增 3 个 GIN 索引：

- `idx_papers_title_fts`
- `idx_papers_abstract_fts`
- `idx_keywords_keyword_fts`

部署顺序仍然建议：

1. 在 Supabase SQL Editor 中重新执行最新的 `migrate_db.sql`
2. 验证两个 RPC 查询有结果
3. 重启后端服务

可用下面的 SQL 做验证：

```sql
select *
from search_papers_optimized(
  'transformers',
  'NeurIPS 2025',
  true,
  true,
  true,
  5,
  0
);

select count_papers_optimized(
  'transformers',
  'NeurIPS 2025',
  true,
  true,
  true
);
```

如果第二阶段 SQL 尚未部署，后端仍会回退到第一阶段搜索逻辑，但不会获得 FTS 的词干化和相关性排序提升。

### 2. 导入数据

运行导入脚本，从爬取的数据中加载论文：

```bash
# 导入 NeurIPS 2025 论文
python scripts/import_papers.py --conference neurips_2025

# 导入 ICLR 2026 论文
python scripts/import_papers.py --conference iclr_2026
```

**环境要求：**
- 脚本会自动从 `backend/.env` 读取 Supabase 凭证
- 需要安装 `python-dotenv` 依赖：`pip install python-dotenv`

## 已完成的修改

### 后端
- 更新 `database.py`：
  - `get_paper()` 现在会联表查询 authors 和 keywords
  - `save_paper()` 现在会保存到 authors 和 keywords 表
  - 删除了 `get_recent_papers()` 函数

- 更新 `app.py`：
  - 删除了 `/papers/recent` 端点

### 前端
- 更新 `index.html`：
  - 删除了"最近分析"部分

- 更新 `home.js`：
  - 删除了加载最近论文的逻辑

## 新数据库结构

**papers 表：**
- id (TEXT, 主键)
- title (TEXT)
- abstract (TEXT)
- venue (TEXT) - 例如："NeurIPS 2025 poster"
- primary_area (TEXT) - 例如："applications"
- llm_response (TEXT)

**authors 表：**
- id (SERIAL, 主键)
- paper_id (TEXT, 外键)
- author_name (TEXT)
- author_order (INTEGER)

**keywords 表：**
- id (SERIAL, 主键)
- paper_id (TEXT, 外键)
- keyword (TEXT)
