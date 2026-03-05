import requests
import json
import time
import csv
from typing import List, Dict, Optional, Union
from urllib.parse import urlencode

try:
    from tqdm import tqdm
except ImportError:
    print("提示: 安装 tqdm 库以获得进度条显示: pip install tqdm")
    # 创建假的 tqdm 函数
    def tqdm(iterable, **kwargs):
        return iterable

# API 配置
API_BASE_URL = "https://api2.openreview.net/notes"
LIMIT = 25  # 每页论文数量
INITIAL_DELAY = 0.8  # 初始请求延迟（秒）
OUTPUT_FORMAT = "json"  # 输出格式: "json" 或 "csv"

# 可以修改为以下值来获取不同类型的论文：
# - "NeurIPS 2025 poster" (海报论文)
# - "NeurIPS 2025 oral" (口头报告论文)
# - "NeurIPS 2025 spotlight" (亮点论文)
PAPER_VENUE = "NeurIPS 2025 spotlight"

# API 请求参数配置
API_PARAMS = {
    "content.venue": PAPER_VENUE,
    "details": "replyCount,presentation,writable",
    "domain": "NeurIPS.cc/2025/Conference",
    "invitation": "NeurIPS.cc/2025/Conference/-/Submission",
    "limit": LIMIT
    # "offset" 参数会在请求时动态添加
}

# 请求头
HEADERS = {
    "Accept": "application/json,text/*;q=0.99",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Referer": "https://openreview.net/",
    "Origin": "https://openreview.net"
}


class NIPS25Crawler:
    """NeurIPS 2025 Poster Papers Crawler"""

    def __init__(self, limit: int = 25, output_format: str = "json", delay: float = 0.8):
        """
        初始化爬虫

        Args:
            limit: 每页获取的论文数量
            output_format: 输出格式 ("json" 或 "csv")
            delay: API请求延迟时间（秒）
        """
        self.limit = limit
        self.output_format = output_format.lower()
        self.delay = delay
        self.total_papers = 0

        # 根据 PAPER_VENUE 动态生成输出文件名
        # 提取论文类型（poster/oral/spotlight）并用于文件名
        paper_type = PAPER_VENUE.split()[-1].lower()  # 获取最后一个单词（poster/oral/spotlight）
        self.output_file = f"nips25_{paper_type}_papers.{self.output_format}"

    def construct_api_url(self, offset: int = 0) -> str:
        """
        构建API请求URL

        Args:
            offset: 分页偏移量

        Returns:
            完整的API URL
        """
        # 使用 API_PARAMS 配置，并动态添加 offset 参数
        params = API_PARAMS.copy()
        params["offset"] = offset
        params["limit"] = self.limit  # 使用实例的 limit 值
        return f"{API_BASE_URL}?{urlencode(params)}"

    def fetch_page(self, offset: int) -> Optional[Dict]:
        """
        获取指定分页的数据

        Args:
            offset: 分页偏移量

        Returns:
            API响应数据或None（请求失败时）
        """
        url = self.construct_api_url(offset)

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()

            data = response.json()

            # 如果是第一页，获取总数
            if offset == 0:
                self.total_papers = data.get("count", 0)

            return data

        except requests.exceptions.RequestException as e:
            print(f"\n❌ 请求失败 (offset={offset}): {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON解析失败 (offset={offset}): {e}")
            return None
        except Exception as e:
            print(f"\n❌ 未知错误 (offset={offset}): {e}")
            return None

    def extract_paper_info(self, paper: Union[Dict, object]) -> Dict:
        """
        从论文对象中提取所需信息

        Args:
            paper: 论文对象

        Returns:
            包含提取的信息的字典
        """
        paper_data = {}

        # 基本信息
        paper_data["paper_id"] = paper.get("id", "")
        paper_data["forum_url"] = f"https://openreview.net/forum?id={paper.get('id', '')}"
        paper_data["number"] = paper.get("number")
        paper_data["version"] = paper.get("version")

        # 时间戳（转换为可读格式）
        cdate_timestamp = paper.get("cdate")
        if cdate_timestamp:
            paper_data["submission_date"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(cdate_timestamp / 1000)
            )
        else:
            paper_data["submission_date"] = ""

        # 内容字段
        content = paper.get("content", {})

        paper_data["title"] = content.get("title", {}).get("value", "") if isinstance(content.get("title"), dict) else content.get("title", "")

        authors = content.get("authors", {})
        if isinstance(authors, dict):
            paper_data["authors"] = authors.get("value", [])
        else:
            paper_data["authors"] = authors if isinstance(authors, list) else []

        abstract = content.get("abstract", {})
        if isinstance(abstract, dict):
            paper_data["abstract"] = abstract.get("value", "")
        else:
            paper_data["abstract"] = abstract or ""

        keywords = content.get("keywords", {})
        if isinstance(keywords, dict):
            paper_data["keywords"] = keywords.get("value", [])
        else:
            paper_data["keywords"] = keywords if isinstance(keywords, list) else []

        primary_area = content.get("primary_area", {})
        if isinstance(primary_area, dict):
            paper_data["primary_area"] = primary_area.get("value", "")
        else:
            paper_data["primary_area"] = primary_area or ""

        # PDF URL 构建
        # NeurIPS 2025 的 PDF 链接有两种格式：
        # 1. https://openreview.net/pdf?id={paper_id}
        # 2. https://openreview.net/attachment?id={paper_id}&name=pdf
        # 我们优先使用 API 返回的 pdf 路径，如果不可用则使用 attachment 格式
        pdf_path = content.get("pdf", {}).get("value", "") if isinstance(content.get("pdf"), dict) else content.get("pdf", "")
        paper_id = paper.get('id', '')

        if pdf_path.startswith("/"):
            # 使用 API 返回的完整路径
            paper_data["pdf_url"] = f"https://openreview.net{pdf_path}"
        elif paper_id:
            # 使用 attachment 格式作为备选: https://openreview.net/attachment?id={paper_id}&name=pdf
            paper_data["pdf_url"] = f"https://openreview.net/attachment?id={paper_id}&name=pdf"
        else:
            paper_data["pdf_url"] = ""

        # TLDR (简要总结)
        tldr = content.get("TLDR", {})
        if isinstance(tldr, dict):
            paper_data["tldr"] = tldr.get("value", "")
        else:
            paper_data["tldr"] = tldr or ""

        # 回复数量
        details = paper.get("details", {})
        paper_data["reply_count"] = details.get("replyCount", 0) if details else 0

        # 会议场馆
        venue = content.get("venue", {})
        if isinstance(venue, dict):
            paper_data["venue"] = venue.get("value", "")
        else:
            paper_data["venue"] = venue or ""

        # venueid
        venueid = content.get("venueid", {})
        if isinstance(venueid, dict):
            paper_data["venueid"] = venueid.get("value", "")
        else:
            paper_data["venueid"] = venueid or ""

        return paper_data

    def process_response(self, data: Dict) -> List[Dict]:
        """
        处理API响应数据，提取论文列表

        Args:
            data: API响应数据

        Returns:
            论文信息列表
        """
        papers = []
        notes = data.get("notes", [])

        for paper in notes:
            paper_info = self.extract_paper_info(paper)
            papers.append(paper_info)

        return papers

    def fetch_all_papers(self) -> List[Dict]:
        """
        获取所有论文数据

        Returns:
            所有论文的信息列表
        """
        all_papers = []
        offset = 0
        successful_requests = 0
        failed_requests = 0

        print("=" * 60)
        print(" NeurIPS 2025 Poster Papers Crawler")
        print("=" * 60)
        print(f"论文类型: {API_PARAMS.get('content.venue')}")
        print(f"输出格式: {self.output_format.upper()}")
        print(f"输出文件: {self.output_file}")
        print("-" * 60)
        print("🔍 正在获取第一批数据以确定总数量...")

        # 第一页请求
        first_page = self.fetch_page(offset)
        if not first_page:
            print("❌ 无法获取第一批数据，请检查网络连接或API状态")
            return []

        print(f"✅ 发现 {self.total_papers} 篇论文")

        if self.total_papers == 0:
            print("⚠️ 未找到任何论文")
            return []

        total_pages = (self.total_papers + self.limit - 1) // self.limit

        print(f"📄 需要获取 {total_pages} 页数据 (每页 {self.limit} 篇)")
        print("⏳ 开始获取数据...")
        print("-" * 60)

        try:
            from tqdm import tqdm
            use_tqdm = True
        except ImportError:
            use_tqdm = False

        if use_tqdm:
            pbar = tqdm(total=self.total_papers, desc="获取进度", unit="paper")
        else:
            pbar = None

        current_count = 0

        # 处理第一页数据
        papers = self.process_response(first_page)
        all_papers.extend(papers)
        successful_requests += 1
        current_count += len(papers)

        if pbar:
            pbar.update(len(papers))
        else:
            print(f"  进度: {current_count}/{self.total_papers} 篇")

        offset += self.limit

        # 处理剩余页面
        while offset < self.total_papers:
            page_data = self.fetch_page(offset)

            if page_data:
                papers = self.process_response(page_data)
                all_papers.extend(papers)
                successful_requests += 1
                current_count += len(papers)

                if pbar:
                    pbar.update(len(papers))
                else:
                    print(f"  进度: {current_count}/{self.total_papers} 篇")
            else:
                failed_requests += 1
                print(f"\n⚠️  跳过 offset={offset} (请求失败)")

            offset += self.limit
            time.sleep(min(self.delay + offset * 0.0001, 2.0))

        if pbar:
            pbar.close()

        print("-" * 60)
        print(f"✅ 数据获取完成!")
        print(f"   - 成功: {successful_requests} 页")
        print(f"   - 失败: {failed_requests} 页")
        print(f"   - 总计: {len(all_papers)} / {self.total_papers} 篇论文")

        return all_papers

    def save_as_json(self, papers: List[Dict]) -> None:
        """
        保存数据为 JSON 格式

        Args:
            papers: 论文数据列表
        """
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(papers, f, indent=2, ensure_ascii=False)
            print(f"💾 JSON 文件已保存: {self.output_file}")
            print(f"   文件大小: {len(json.dumps(papers)) / 1024:.2f} KB")
        except Exception as e:
            print(f"❌ 保存 JSON 文件失败: {e}")

    def save_as_csv(self, papers: List[Dict]) -> None:
        """
        保存数据为 CSV 格式

        Args:
            papers: 论文数据列表
        """
        if not papers:
            print("⚠️ 没有数据可保存")
            return

        try:
            fieldnames = [
                "paper_id", "number", "version", "title", "authors", "abstract",
                "keywords", "primary_area", "venue", "venueid", "tldr",
                "pdf_url", "forum_url", "submission_date", "reply_count"
            ]

            with open(self.output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for paper in papers:
                    row = paper.copy()
                    row["authors"] = "; ".join(row["authors"])
                    row["keywords"] = "; ".join(row["keywords"])
                    writer.writerow(row)

            print(f"💾 CSV 文件已保存: {self.output_file}")

            # 计算文件大小
            import os
            file_size = os.path.getsize(self.output_file)
            print(f"   文件大小: {file_size / 1024:.2f} KB")

        except Exception as e:
            print(f"❌ 保存 CSV 文件失败: {e}")

    def save_data(self, papers: List[Dict]) -> None:
        """
        根据配置的格式保存数据

        Args:
            papers: 论文数据列表
        """
        if self.output_format == "json":
            self.save_as_json(papers)
        elif self.output_format == "csv":
            self.save_as_csv(papers)
        else:
            print(f"⚠️ 不支持的格式: {self.output_format}")
            print("💾 将使用 JSON 格式作为回退选项")
            self.output_file = "nips25_papers.json"
            self.save_as_json(papers)


def main():
    """主函数"""

    try:
        # 创建爬虫实例
        crawler = NIPS25Crawler(limit=LIMIT, output_format=OUTPUT_FORMAT, delay=INITIAL_DELAY)

        # 获取所有论文
        papers = crawler.fetch_all_papers()

        if papers:
            # 保存数据
            crawler.save_data(papers)
            print("-" * 60)
            print("✨ 所有任务完成!")
            print("=" * 60)
        else:
            print("⚠️ 未获取到任何数据")
            return 1

    except KeyboardInterrupt:
        print("\n\n❌ 用户中断操作")
        print("⚠️ 部分数据可能已获取但未保存")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())