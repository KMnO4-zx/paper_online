#!/usr/bin/env python3
"""Build import-ready CVPR 2026 JSONL from the CVF Open Access site."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, as_completed
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests


REPO_ROOT = Path(__file__).resolve().parent.parent
CVF_BASE_URL = "https://openaccess.thecvf.com"
DEFAULT_LIST_URL = f"{CVF_BASE_URL}/CVPR2026?day=all"
CONFERENCE_ID = "cvpr_2026"
CONFERENCE_VENUE = "CVPR 2026"
PRIMARY_AREA = "Computer Vision and Pattern Recognition"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "crawled_data" / CONFERENCE_ID / "main_papers.jsonl"
DEFAULT_CACHE_PATH = REPO_ROOT / "crawled_data" / CONFERENCE_ID / "cvf_cache.json"
USER_AGENT = "paper-online/0.1 (CVPR 2026 metadata importer)"


@dataclass(frozen=True)
class CvfPaperLink:
    order: int
    html_url: str


class CvfListParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self._seen: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        if not href.startswith("/content/CVPR2026/html/"):
            return
        url = urljoin(CVF_BASE_URL, href)
        if url in self._seen:
            return
        self._seen.add(url)
        self.links.append(url)


class CvfDetailParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, list[str]] = {}
        self.links: list[str] = []
        self.sections: dict[str, list[str]] = {
            "abstract": [],
            "authors": [],
            "papertitle": [],
            "bibtex": [],
        }
        self._capture: str | None = None
        self._capture_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "meta":
            name = attrs_dict.get("name")
            content = attrs_dict.get("content")
            if name and content:
                self.meta.setdefault(name, []).append(_clean_text(content))
            return

        if tag == "a":
            href = attrs_dict.get("href") or ""
            if href.startswith("/content/CVPR2026/"):
                self.links.append(urljoin(CVF_BASE_URL, href))
            return

        if tag == "div":
            element_id = attrs_dict.get("id")
            classes = set((attrs_dict.get("class") or "").split())
            if element_id in {"abstract", "authors", "papertitle"}:
                self._capture = element_id
                self._capture_depth = 1
            elif "bibref" in classes:
                self._capture = "bibtex"
                self._capture_depth = 1
            elif self._capture:
                self._capture_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self._capture:
            self._capture_depth -= 1
            if self._capture_depth <= 0:
                self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture:
            self.sections[self._capture].append(data)


def parse_cvf_list(html_text: str) -> list[CvfPaperLink]:
    parser = CvfListParser()
    parser.feed(html_text)
    return [
        CvfPaperLink(order=index, html_url=url)
        for index, url in enumerate(parser.links, start=1)
    ]


def load_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"CVF cache is not valid JSON: {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise SystemExit(f"CVF cache must be a JSON object: {path}")
    return {key: value for key, value in raw.items() if isinstance(value, dict)}


def save_cache(path: Path, cache: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(sorted(cache.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fetch_text(session: requests.Session, url: str, timeout: tuple[int, int] = (10, 30)) -> str:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 3:
                time.sleep(2**attempt)
                continue
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2**attempt)
                continue
    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def fetch_detail_records(
    links: list[CvfPaperLink],
    cache: dict[str, dict[str, Any]],
    cache_path: Path,
    *,
    workers: int = 8,
    batch_size: int = 100,
    sleep_seconds: float = 0.0,
) -> dict[str, dict[str, Any]]:
    missing = [link for link in links if link.html_url not in cache]
    if not missing:
        return cache

    def fetch_one(link: CvfPaperLink) -> tuple[str, dict[str, Any]]:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        html_text = fetch_text(session, link.html_url)
        if sleep_seconds:
            time.sleep(sleep_seconds)
        return link.html_url, parse_cvf_detail(link, html_text)

    completed = 0
    errors: list[str] = []
    chunk_size = max(1, batch_size)
    for start in range(0, len(missing), chunk_size):
        chunk = missing[start : start + chunk_size]
        executor = ThreadPoolExecutor(max_workers=max(1, workers))
        futures = {executor.submit(fetch_one, link): link for link in chunk}
        try:
            try:
                for future in as_completed(futures, timeout=180):
                    link = futures[future]
                    try:
                        url, detail = future.result()
                    except Exception as exc:
                        errors.append(f"{link.html_url}: {exc}")
                        continue
                    cache[url] = detail
                    completed += 1
            except FuturesTimeoutError:
                for future, link in futures.items():
                    if not future.done():
                        future.cancel()
                        errors.append(f"{link.html_url}: timed out while waiting for batch completion")
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        save_cache(cache_path, cache)
        print(f"Fetched CVF details for {completed}/{len(missing)} missing paper(s)", flush=True)

    if errors:
        preview = "\n".join(errors[:10])
        raise RuntimeError(f"Failed to fetch {len(errors)} CVF detail page(s):\n{preview}")

    save_cache(cache_path, cache)
    return cache


def parse_cvf_detail(link: CvfPaperLink, html_text: str) -> dict[str, Any]:
    parser = CvfDetailParser()
    parser.feed(html_text)

    title = _first_meta(parser, "citation_title") or _section_text(parser, "papertitle")
    authors = _authors_from_visible_text(_section_text(parser, "authors"))
    if not authors:
        authors = [_normalize_meta_author(author) for author in parser.meta.get("citation_author", []) if author]

    pdf_url = _first_meta(parser, "citation_pdf_url") or _first_link_matching(parser.links, "/papers/")
    first_page = _first_meta(parser, "citation_firstpage")
    last_page = _first_meta(parser, "citation_lastpage")
    pages = f"{first_page}-{last_page}" if first_page and last_page else ""

    return {
        "order": link.order,
        "html_url": link.html_url,
        "id": paper_id_from_html_url(link.html_url, title),
        "title": title,
        "authors": authors,
        "abstract": _section_text(parser, "abstract"),
        "pdf": pdf_url,
        "supplemental": _first_link_matching(parser.links, "/supplemental/"),
        "pages": pages,
        "bibtex": _section_text(parser, "bibtex"),
    }


def paper_id_from_html_url(html_url: str, title: str) -> str:
    parsed = urlparse(html_url)
    stem = Path(parsed.path).stem
    stem = re.sub(r"_CVPR_2026_paper$", "", stem)
    slug_source = stem or title
    slug = re.sub(r"[^a-z0-9]+", "-", slug_source.casefold()).strip("-")[:90]
    digest = hashlib.sha1(html_url.encode("utf-8")).hexdigest()[:8]
    return f"cvpr2026-{slug}-{digest}"


def build_jsonl_record(detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": detail["id"],
        "forum": detail["html_url"],
        "license": "CVF Open Access",
        "domain": CONFERENCE_VENUE,
        "content": {
            "title": {"value": detail["title"]},
            "authors": {"value": detail["authors"]},
            "keywords": {"value": []},
            "abstract": {"value": detail["abstract"]},
            "primary_area": {"value": PRIMARY_AREA},
            "venue": {"value": CONFERENCE_VENUE},
            "pdf": {"value": detail["pdf"]},
            "html_url": {"value": detail["html_url"]},
            "supplemental": {"value": detail.get("supplemental") or ""},
            "pages": {"value": detail.get("pages") or ""},
            "source": {"value": "CVF Open Access"},
            "sort_order": {"value": detail["order"]},
        },
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _first_meta(parser: CvfDetailParser, name: str) -> str:
    values = parser.meta.get(name) or []
    return values[0] if values else ""


def _first_link_matching(links: list[str], pattern: str) -> str:
    for link in links:
        if pattern in link:
            return link
    return ""


def _section_text(parser: CvfDetailParser, key: str) -> str:
    return _clean_text(" ".join(parser.sections.get(key) or []))


def _authors_from_visible_text(value: str) -> list[str]:
    if not value:
        return []
    author_text = value.split("; Proceedings", 1)[0].strip()
    return [author.strip() for author in author_text.split(",") if author.strip()]


def _normalize_meta_author(value: str) -> str:
    if "," not in value:
        return _clean_text(value)
    last, rest = value.split(",", 1)
    return _clean_text(f"{rest} {last}")


def _clean_text(value: str | None) -> str:
    return " ".join((value or "").split()).strip()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build crawled_data/cvpr_2026 JSONL from CVF Open Access")
    parser.add_argument("--list-url", default=DEFAULT_LIST_URL, help="CVF CVPR 2026 all-papers URL")
    parser.add_argument("--list-html", type=Path, help="Use a local CVF all-papers HTML file")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output JSONL path")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE_PATH, help="Parsed CVF detail cache JSON path")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent detail page fetches")
    parser.add_argument("--batch-size", type=int, default=100, help="Detail pages to process per batch")
    parser.add_argument("--sleep-seconds", type=float, default=0.0, help="Optional sleep after each detail fetch")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.list_html:
        list_html = args.list_html.read_text(encoding="utf-8")
    else:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        list_html = fetch_text(session, args.list_url)

    links = parse_cvf_list(list_html)
    if not links:
        print("No CVPR 2026 paper links found in CVF source", file=sys.stderr)
        return 1

    cache = load_cache(args.cache)
    cache = fetch_detail_records(
        links,
        cache,
        args.cache,
        workers=max(1, args.workers),
        batch_size=max(1, args.batch_size),
        sleep_seconds=max(0.0, args.sleep_seconds),
    )
    records = [build_jsonl_record(cache[link.html_url]) for link in links]
    write_jsonl(args.output, records)

    with_abstract = sum(1 for record in records if record["content"]["abstract"]["value"])
    with_pdf = sum(1 for record in records if record["content"]["pdf"]["value"])
    print(f"Wrote {len(records)} CVPR 2026 papers to {args.output}")
    print(f"Abstracts: {with_abstract}/{len(records)}")
    print(f"PDF URLs: {with_pdf}/{len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
