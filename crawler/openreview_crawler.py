import requests
import json
import time
import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlencode

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

HEADERS = {
    "Accept": "application/json,text/*;q=0.99",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://openreview.net/",
    "Origin": "https://openreview.net"
}

class OpenReviewCrawler:
    def __init__(self, config: Dict, venue_type: Optional[str] = None):
        self.config = config
        self.conf = config['conference']
        self.settings = config['settings']
        self.venues = [v for v in config['venues'] if not venue_type or v['type'] == venue_type]
        self.total_papers = 0

    def construct_api_url(self, venue: str, offset: int) -> str:
        params = {
            "content.venue": venue,
            "details": "replyCount,presentation,writable",
            "domain": self.conf['domain'],
            "invitation": self.conf['invitation'],
            "limit": self.settings['limit'],
            "offset": offset
        }
        return f"{self.settings['api_base_url']}?{urlencode(params)}"

    def fetch_page(self, venue: str, offset: int) -> Optional[Dict]:
        url = self.construct_api_url(venue, offset)
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"\n❌ 请求失败 (offset={offset}): {e}")
            return None

    def fetch_venue_papers(self, venue_config: Dict) -> List[Dict]:
        venue = venue_config['venue']
        venue_type = venue_config['type']
        all_papers = []
        offset = 0

        print(f"\n🔍 获取 {venue} 论文...")

        first_page = self.fetch_page(venue, offset)
        if not first_page:
            print(f"❌ 无法获取 {venue} 数据")
            return []

        total = first_page.get("count", 0)
        print(f"✅ 发现 {total} 篇论文")

        if total == 0:
            return []

        limit = self.settings['limit']
        try:
            pbar = tqdm(total=total, desc=f"{venue_type}", unit="paper")
            use_tqdm = True
        except:
            use_tqdm = False
            pbar = None

        # 处理第一页
        all_papers.extend(first_page.get("notes", []))
        if pbar:
            pbar.update(len(first_page.get("notes", [])))

        offset += limit

        # 处理剩余页面
        while offset < total:
            page_data = self.fetch_page(venue, offset)
            if page_data:
                notes = page_data.get("notes", [])
                all_papers.extend(notes)
                if pbar:
                    pbar.update(len(notes))
            else:
                print(f"\n⚠️ 跳过 offset={offset}")

            offset += limit
            time.sleep(min(self.settings['initial_delay'] + offset * 0.0001, self.settings['max_delay']))

        if pbar:
            pbar.close()

        return all_papers

    def save_jsonl(self, papers: List[Dict], output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for paper in papers:
                    f.write(json.dumps(paper, ensure_ascii=False) + '\n')
            print(f"💾 已保存: {output_path} ({len(papers)} 篇)")
        except Exception as e:
            print(f"❌ 保存失败: {e}")

    def crawl(self):
        print("=" * 60)
        print(f" {self.conf['name']} OpenReview Crawler")
        print("=" * 60)

        base_dir = Path("crawled_data") / self.conf['output_dir']

        for venue_config in self.venues:
            papers = self.fetch_venue_papers(venue_config)
            if papers:
                output_file = base_dir / f"{venue_config['type']}_papers.jsonl"
                self.save_jsonl(papers, output_file)

        print("\n✨ 完成!")

def load_config(config_name: str) -> Dict:
    config_path = Path(__file__).parent / "configs" / f"{config_name}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="OpenReview 通用爬虫")
    parser.add_argument("--config", required=True, help="配置文件名 (不含.yaml)")
    parser.add_argument("--venue", help="指定场次类型 (poster/oral/spotlight)")
    parser.add_argument("--list", action="store_true", help="列出所有场次")

    args = parser.parse_args()

    config = load_config(args.config)

    if args.list:
        print(f"\n{config['conference']['name']} 可用场次:")
        for v in config['venues']:
            print(f"  - {v['type']}: {v['venue']}")
        return 0

    crawler = OpenReviewCrawler(config, args.venue)
    crawler.crawl()
    return 0

if __name__ == "__main__":
    exit(main())
