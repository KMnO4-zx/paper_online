import json
import os
import requests
import logging
import re
import tiktoken
import time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TIMEOUT = 30
MAX_RETRIES = 3
LLM_CONTENT_TOKEN_LIMIT = 180000
_TOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")

HEADERS = {
    "Accept": "application/json,text/*;q=0.99",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Referer": "https://openreview.net/",
    "Origin": "https://openreview.net"
}

DEFAULT_PAPER_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "paper_cache"
OPENREVIEW_PDF_URL_PREFIX = "https://openreview.net/pdf?id="
_OPENREVIEW_URL_PATTERN = re.compile(r"^https://openreview\.net/(?:attachment|pdf)\?")


class ReaderError(Exception):
    """Jina Reader 请求失败"""
    pass


class OpenReviewError(Exception):
    """OpenReview API 请求失败"""
    pass


def get_openreview_pdf_url(paper_id: str) -> str:
    return f"{OPENREVIEW_PDF_URL_PREFIX}{paper_id}"


def normalize_paper_pdf_url(paper_id: str, pdf_url: str | None) -> str | None:
    if pdf_url is None:
        return None

    normalized_url = pdf_url.strip()
    if not normalized_url:
        return None

    # Normalize all OpenReview PDF variants to one canonical form so DB rows
    # and cache metadata stay stable.
    if _OPENREVIEW_URL_PATTERN.match(normalized_url):
        return get_openreview_pdf_url(paper_id)

    return normalized_url


def _get_paper_cache_dir() -> Path:
    return Path(os.getenv("PAPER_CONTENT_CACHE_DIR", str(DEFAULT_PAPER_CACHE_DIR)))


def _get_paper_cache_paths(paper_id: str) -> tuple[Path, Path]:
    safe_paper_id = re.sub(r"[^A-Za-z0-9._-]", "_", paper_id)
    cache_dir = _get_paper_cache_dir()
    return (
        cache_dir / f"{safe_paper_id}.txt",
        cache_dir / f"{safe_paper_id}.meta.json",
    )


def has_cached_paper_content(paper_id: str, pdf_url: str | None = None) -> bool:
    pdf_url = normalize_paper_pdf_url(paper_id, pdf_url)
    content_path, meta_path = _get_paper_cache_paths(paper_id)
    if not content_path.exists():
        return False

    try:
        if content_path.stat().st_size <= 0:
            return False
    except OSError:
        return False

    if pdf_url and meta_path.exists():
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("论文正文缓存元数据损坏，忽略缓存: %s", meta_path)
            return False

        cached_pdf_url = normalize_paper_pdf_url(paper_id, metadata.get("pdf_url"))
        if cached_pdf_url and cached_pdf_url != pdf_url:
            logger.info("论文 %s 的 PDF 地址已变化，重新抓取正文缓存", paper_id)
            return False

    return True


def get_cached_paper_content(paper_id: str, pdf_url: str | None = None) -> str | None:
    pdf_url = normalize_paper_pdf_url(paper_id, pdf_url)
    content_path, _ = _get_paper_cache_paths(paper_id)
    if not has_cached_paper_content(paper_id, pdf_url):
        logger.info("论文正文缓存未命中: %s", paper_id)
        return None

    try:
        content = content_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("读取论文正文缓存失败 %s: %s", content_path, exc)
        return None

    if not content.strip():
        logger.warning("论文正文缓存为空，忽略缓存: %s", content_path)
        return None

    logger.info("论文正文缓存命中: %s", paper_id)
    return content


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def cache_paper_content(paper_id: str, pdf_url: str, content: str) -> None:
    if not content.strip():
        logger.warning("论文正文为空，跳过缓存: %s", paper_id)
        return

    normalized_pdf_url = normalize_paper_pdf_url(paper_id, pdf_url) or pdf_url
    content_path, meta_path = _get_paper_cache_paths(paper_id)
    metadata = {
        "paper_id": paper_id,
        "pdf_url": normalized_pdf_url,
        "source": "jina_reader",
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "size_bytes": len(content.encode("utf-8")),
    }

    try:
        _atomic_write_text(content_path, content)
        _atomic_write_text(
            meta_path,
            json.dumps(metadata, ensure_ascii=False, indent=2),
        )
        logger.info("已缓存论文正文: %s -> %s", paper_id, content_path)
    except OSError as exc:
        logger.warning("写入论文正文缓存失败 %s: %s", content_path, exc)


def get_or_cache_paper_content(paper_id: str, pdf_url: str) -> str:
    normalized_pdf_url = normalize_paper_pdf_url(paper_id, pdf_url) or pdf_url
    cached_content = get_cached_paper_content(paper_id, normalized_pdf_url)
    if cached_content is not None:
        return cached_content

    content = reader(normalized_pdf_url)
    cache_paper_content(paper_id, normalized_pdf_url, content)
    return content


def truncate_content_for_llm(text: str, max_tokens: int = LLM_CONTENT_TOKEN_LIMIT) -> str:
    # Some PDFs contain strings like "<|endoftext|>" literally.
    # They should be treated as normal text instead of special tokens.
    token_ids = _TOKEN_ENCODING.encode(text, disallowed_special=())
    token_count = len(token_ids)

    if token_count <= max_tokens:
        logger.info(f"LLM content within token limit: {token_count} <= {max_tokens}")
        return text

    truncated_text = _TOKEN_ENCODING.decode(token_ids[:max_tokens])
    logger.warning(
        "LLM content truncated by tokens: original=%s, kept=%s",
        token_count,
        max_tokens,
    )
    return truncated_text


def reader(url: str) -> str:
    target_url = "https://r.jina.ai/" + url

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(target_url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.Timeout:
            logger.warning(f"Jina Reader 超时 (尝试 {attempt + 1}/{MAX_RETRIES})")
        except requests.RequestException as e:
            logger.warning(f"Jina Reader 请求失败: {e} (尝试 {attempt + 1}/{MAX_RETRIES})")

        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)

    raise ReaderError(f"Jina Reader 请求失败，已重试 {MAX_RETRIES} 次: {url}")

def get_openreview_info(paper_id: str) -> dict | None:
    url = f"https://api2.openreview.net/notes?id={paper_id}"

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if not data.get("notes"):
                return None

            note = data["notes"][0]
            content = note.get("content", {})

            return {
                "id": note.get("id"),
                "title": content.get("title", {}).get("value"),
                "abstract": content.get("abstract", {}).get("value"),
                "authors": content.get("authors", {}).get("value", []),
                "keywords": content.get("keywords", {}).get("value", []),
                "primary_area": content.get("primary_area", {}).get("value"),
                "venue": content.get("venue", {}).get("value"),
                "pdf": get_openreview_pdf_url(note["id"]),
            }
        except requests.Timeout:
            logger.warning(f"OpenReview API 超时 (尝试 {attempt + 1}/{MAX_RETRIES})")
        except requests.RequestException as e:
            logger.warning(f"OpenReview API 请求失败: {e} (尝试 {attempt + 1}/{MAX_RETRIES})")

        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)

    raise OpenReviewError(f"OpenReview API 请求失败，已重试 {MAX_RETRIES} 次: {paper_id}")



if __name__ == "__main__":
    sample_url = "https://openreview.net/pdf?id=uq6UWRgzMr"
    # content = reader(sample_url)
    # print(content)

    # paper_id = "uq6UWRgzMr"
    # info = get_openreview_info(paper_id)
    # print(info)
