import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any
from urllib.parse import unquote, urlparse

import requests

logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_ABS_URL_PREFIX = "https://arxiv.org/abs/"
ARXIV_PDF_URL_PREFIX = "https://arxiv.org/pdf/"
ARXIV_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"

_MODERN_ARXIV_ID_PATTERN = re.compile(
    r"^(?:arxiv:)?(?P<id>\d{4}\.\d{4,5})(?:v\d+)?$",
    re.IGNORECASE,
)
_LEGACY_ARXIV_ID_PATTERN = re.compile(
    r"^(?:arxiv:)?(?P<id>[a-z-]+(?:\.[a-z-]+)?/\d{7})(?:v\d+)?$",
    re.IGNORECASE,
)


class ArxivError(Exception):
    """Base arXiv integration error."""


class ArxivInvalidInputError(ArxivError):
    """The user input is not an arXiv URL or ID."""


class ArxivNotFoundError(ArxivError):
    """The arXiv API did not return article metadata."""


def _collapse_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _candidate_from_url(raw_value: str) -> str | None:
    parsed = urlparse(raw_value)
    host = parsed.netloc.casefold()
    if not host or not (host == "arxiv.org" or host.endswith(".arxiv.org")):
        return None

    parts = [unquote(part) for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2 or parts[0] not in {"abs", "pdf", "html", "e-print"}:
        return None

    candidate = "/".join(parts[1:])
    if candidate.endswith(".pdf"):
        candidate = candidate[:-4]
    return candidate


def normalize_arxiv_id(raw_value: str) -> str | None:
    value = raw_value.strip()
    if not value:
        return None

    candidate = _candidate_from_url(value) or value
    candidate = candidate.strip()
    if candidate.casefold().startswith("arxiv:"):
        candidate = candidate.split(":", 1)[1].strip()
    if candidate.endswith(".pdf"):
        candidate = candidate[:-4]

    for pattern in (_MODERN_ARXIV_ID_PATTERN, _LEGACY_ARXIV_ID_PATTERN):
        match = pattern.match(candidate)
        if match:
            return match.group("id").casefold()

    return None


def extract_arxiv_id(raw_value: str) -> str:
    arxiv_id = normalize_arxiv_id(raw_value)
    if not arxiv_id:
        raise ArxivInvalidInputError("请输入有效的 arXiv 链接或 ID")
    return arxiv_id


def build_arxiv_paper_id(arxiv_id: str) -> str:
    return f"arxiv:{arxiv_id.replace('/', '_')}"


def arxiv_id_from_paper_id(paper_id: str) -> str | None:
    if not paper_id.startswith("arxiv:"):
        return None
    return normalize_arxiv_id(paper_id.removeprefix("arxiv:").replace("_", "/"))


def build_arxiv_abs_url(arxiv_id: str) -> str:
    return f"{ARXIV_ABS_URL_PREFIX}{arxiv_id}"


def build_arxiv_pdf_url(arxiv_id: str) -> str:
    return f"{ARXIV_PDF_URL_PREFIX}{arxiv_id}"


def _entry_text(entry: ET.Element, tag: str) -> str:
    element = entry.find(f"{ATOM_NS}{tag}")
    return _collapse_text(element.text if element is not None else None)


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("无法解析 arXiv 时间戳: %s", value)
        return None


def _entry_arxiv_id(entry: ET.Element) -> str | None:
    entry_id = _entry_text(entry, "id")
    if not entry_id:
        return None
    parsed = urlparse(entry_id)
    if parsed.path.startswith("/abs/"):
        return normalize_arxiv_id(unquote(parsed.path.removeprefix("/abs/")))
    return normalize_arxiv_id(entry_id)


def _entry_pdf_url(entry: ET.Element, arxiv_id: str) -> str:
    for link in entry.findall(f"{ATOM_NS}link"):
        if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
            href = link.attrib.get("href")
            if href:
                return href
    return build_arxiv_pdf_url(arxiv_id)


def _entry_categories(entry: ET.Element) -> list[str]:
    categories: list[str] = []
    for category in entry.findall(f"{ATOM_NS}category"):
        term = _collapse_text(category.attrib.get("term"))
        if term and term not in categories:
            categories.append(term)
    return categories


def _entry_authors(entry: ET.Element) -> list[str]:
    authors: list[str] = []
    for author in entry.findall(f"{ATOM_NS}author"):
        name = _collapse_text(author.findtext(f"{ATOM_NS}name"))
        if name:
            authors.append(name)
    return authors


def _entry_optional_text(entry: ET.Element, tag: str) -> str | None:
    value = _collapse_text(entry.findtext(f"{ARXIV_NS}{tag}"))
    return value or None


def _normalize_entry(entry: ET.Element, requested_arxiv_id: str) -> dict[str, Any]:
    title = _entry_text(entry, "title")
    if title == "Error":
        summary = _entry_text(entry, "summary")
        raise ArxivNotFoundError(summary or f"arXiv paper not found: {requested_arxiv_id}")

    arxiv_id = _entry_arxiv_id(entry) or requested_arxiv_id
    paper_id = build_arxiv_paper_id(arxiv_id)
    abstract = _entry_text(entry, "summary")
    categories = _entry_categories(entry)
    primary_category = entry.find(f"{ARXIV_NS}primary_category")
    primary_area = _collapse_text(primary_category.attrib.get("term")) if primary_category is not None else None
    published_raw = _entry_text(entry, "published")
    updated_raw = _entry_text(entry, "updated")
    pdf_url = _entry_pdf_url(entry, arxiv_id)

    return {
        "paper": {
            "id": paper_id,
            "title": title,
            "abstract": abstract,
            "authors": _entry_authors(entry),
            "keywords": categories,
            "pdf": pdf_url,
            "venue": "arXiv",
            "primary_area": primary_area,
        },
        "arxiv": {
            "arxiv_id": arxiv_id,
            "arxiv_url": build_arxiv_abs_url(arxiv_id),
            "pdf_url": pdf_url,
            "published_at": _parse_datetime(published_raw),
            "updated_at": _parse_datetime(updated_raw),
            "primary_category": primary_area,
            "categories": categories,
            "comment": _entry_optional_text(entry, "comment"),
            "journal_ref": _entry_optional_text(entry, "journal_ref"),
            "doi": _entry_optional_text(entry, "doi"),
            "raw": {
                "entry_id": _entry_text(entry, "id"),
                "published": published_raw,
                "updated": updated_raw,
                "categories": categories,
                "primary_category": primary_area,
            },
        },
    }


def parse_arxiv_api_response(payload: str, requested_arxiv_id: str) -> dict[str, Any]:
    root = ET.fromstring(payload)
    entry = root.find(f"{ATOM_NS}entry")
    if entry is None:
        raise ArxivNotFoundError(f"arXiv paper not found: {requested_arxiv_id}")
    return _normalize_entry(entry, requested_arxiv_id)


def fetch_arxiv_paper(raw_value: str) -> dict[str, Any]:
    arxiv_id = extract_arxiv_id(raw_value)
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                ARXIV_API_URL,
                params={"id_list": arxiv_id, "max_results": "1"},
                timeout=ARXIV_TIMEOUT_SECONDS,
                headers={"Accept": "application/atom+xml", "User-Agent": "Paper Insight/1.0"},
            )
            response.raise_for_status()
            return parse_arxiv_api_response(response.text, arxiv_id)
        except requests.Timeout:
            logger.warning("arXiv API 超时 (尝试 %s/%s): %s", attempt + 1, MAX_RETRIES, arxiv_id)
        except requests.RequestException as exc:
            logger.warning("arXiv API 请求失败 (尝试 %s/%s): %s", attempt + 1, MAX_RETRIES, exc)

        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)

    raise ArxivError(f"arXiv API 请求失败，已重试 {MAX_RETRIES} 次: {arxiv_id}")
