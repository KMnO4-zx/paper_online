# OpenReview 通用爬虫

通用的 OpenReview 论文爬虫，支持多个会议和不同论文类型。

## 安装依赖

```bash
pip install requests pyyaml tqdm
```

## 使用方法

### 列出可用场次

```bash
python -m crawler.openreview_crawler --config neurips_2025 --list
```

### 爬取所有场次

```bash
python -m crawler.openreview_crawler --config neurips_2025
```

### 爬取指定场次

```bash
# 爬取 poster 论文
python -m crawler.openreview_crawler --config neurips_2025 --venue poster

# 爬取 oral 论文
python -m crawler.openreview_crawler --config neurips_2025 --venue oral

# 爬取 spotlight 论文
python -m crawler.openreview_crawler --config neurips_2025 --venue spotlight
```

## 配置文件

配置文件位于 `crawler/configs/` 目录，每个会议一个 YAML 文件。

**现有配置：**
- `neurips_2025.yaml` - NeurIPS 2025 (poster, oral, spotlight)
- `iclr_2026.yaml` - ICLR 2026 (poster, oral)

**添加新会议：**

在 `configs/` 目录创建新的 YAML 文件，例如 `icml_2026.yaml`：

```yaml
conference:
  name: "ICML 2026"
  domain: "ICML.cc/2026/Conference"
  invitation: "ICML.cc/2026/Conference/-/Submission"
  output_dir: "icml_2026"

venues:
  - type: "poster"
    venue: "ICML 2026 Poster"
  - type: "oral"
    venue: "ICML 2026 Oral"

settings:
  api_base_url: "https://api2.openreview.net/notes"
  limit: 25
  initial_delay: 0.8
  max_delay: 2.0
```

## 输出格式

输出为 JSONL 格式（每行一个 JSON 对象），保存在 `data/<conference>/` 目录：

```
data/
├── neurips_2025/
│   ├── poster_papers.jsonl
│   ├── oral_papers.jsonl
│   └── spotlight_papers.jsonl
└── iclr_2026/
    ├── poster_papers.jsonl
    └── oral_papers.jsonl
```

每个 JSON 对象包含完整的 API 响应数据（所有字段）：
- `id`, `forum`, `number`, `version`
- `content` (title, authors, abstract, keywords, etc.)
- `details` (replyCount, presentation, etc.)
- `domain`, `invitations`, `signatures`
- 时间戳：`cdate`, `mdate`, `tcdate`, `tmdate`, `pdate`, `odate`

## 示例

```bash
# 1. 查看 NeurIPS 2025 有哪些场次
python -m crawler.openreview_crawler --config neurips_2025 --list

# 2. 爬取 spotlight 论文
python -m crawler.openreview_crawler --config neurips_2025 --venue spotlight

# 3. 验证输出
head -1 data/neurips_2025/spotlight_papers.jsonl | python -m json.tool
```
