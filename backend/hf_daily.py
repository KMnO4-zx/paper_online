import logging
from datetime import date
from typing import Any

import requests

from database import upsert_hf_daily_papers

logger = logging.getLogger(__name__)

HF_DAILY_VENUE = "Hugging Face Daily"
HF_DAILY_TIMEOUT_SECONDS = 30


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _extract_author_names(authors: Any) -> list[str]:
    if not isinstance(authors, list):
        return []

    names: list[str] = []
    for author in authors:
        if isinstance(author, dict):
            name = str(author.get("name") or "").strip()
        else:
            name = str(author).strip()
        if name:
            names.append(name)
    return names


def _extract_keywords(paper: dict[str, Any]) -> list[str]:
    keywords = paper.get("ai_keywords")
    if not isinstance(keywords, list):
        return []
    return [str(keyword).strip() for keyword in keywords if str(keyword).strip()]


def _build_pdf_url(source_id: str) -> str:
    return f"https://arxiv.org/pdf/{source_id}"


def _normalize_entry(raw_entry: dict[str, Any]) -> dict[str, Any] | None:
    paper = raw_entry.get("paper")
    if not isinstance(paper, dict):
        return None

    source_id = str(paper.get("id") or "").strip()
    if not source_id:
        return None

    title = str(paper.get("title") or raw_entry.get("title") or "").strip()
    if not title:
        return None

    summary = str(paper.get("summary") or raw_entry.get("summary") or "").strip()
    upvotes = _as_int(paper.get("upvotes") or raw_entry.get("upvotes"))
    github_stars = paper.get("githubStars")

    return {
        "source_id": source_id,
        "upvotes": upvotes,
        "paper": {
            "id": f"hf:{source_id}",
            "title": title,
            "abstract": summary,
            "keywords": _extract_keywords(paper),
            "pdf": _build_pdf_url(source_id),
            "venue": HF_DAILY_VENUE,
            "authors": _extract_author_names(paper.get("authors")),
        },
        "daily": {
            "upvotes": upvotes,
            "thumbnail": raw_entry.get("thumbnail") or paper.get("thumbnail"),
            "discussion_id": paper.get("discussionId") or raw_entry.get("discussionId"),
            "project_page": paper.get("projectPage") or raw_entry.get("projectPage"),
            "github_repo": paper.get("githubRepo") or raw_entry.get("githubRepo"),
            "github_stars": _as_int(github_stars) if github_stars is not None else None,
            "num_comments": _as_int(raw_entry.get("numComments") or paper.get("numComments")),
            "raw": raw_entry,
        },
    }


def fetch_hf_daily_entries(api_url: str) -> list[dict[str, Any]]:
    response = requests.get(
        api_url,
        timeout=HF_DAILY_TIMEOUT_SECONDS,
        headers={"Accept": "application/json", "User-Agent": "Paper Insight/1.0"},
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("Hugging Face daily papers API did not return a list")
    return [entry for entry in payload if isinstance(entry, dict)]


def select_top_hf_daily_entries(raw_entries: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    by_source_id: dict[str, dict[str, Any]] = {}
    for raw_entry in raw_entries:
        normalized = _normalize_entry(raw_entry)
        if not normalized:
            continue
        existing = by_source_id.get(normalized["source_id"])
        if not existing or normalized["upvotes"] > existing["upvotes"]:
            by_source_id[normalized["source_id"]] = normalized

    selected = sorted(
        by_source_id.values(),
        key=lambda entry: (-entry["upvotes"], entry["paper"]["title"].casefold(), entry["source_id"]),
    )[:max(top_n, 0)]

    for index, entry in enumerate(selected, start=1):
        entry["paper"]["primary_area"] = f"HF Daily Top {index}"
        entry["daily"]["rank"] = index

    return selected


def sync_hf_daily_papers(api_url: str, top_n: int, daily_date: date) -> dict[str, Any]:
    raw_entries = fetch_hf_daily_entries(api_url)
    selected_entries = select_top_hf_daily_entries(raw_entries, top_n)
    analyzable_paper_ids = upsert_hf_daily_papers(daily_date, selected_entries)
    logger.info(
        "HF Daily Papers synced: date=%s selected=%s analyzable=%s",
        daily_date.isoformat(),
        len(selected_entries),
        len(analyzable_paper_ids),
    )
    return {
        "daily_date": daily_date.isoformat(),
        "selected": len(selected_entries),
        "paper_ids": [entry["paper"]["id"] for entry in selected_entries],
        "analyzable_paper_ids": analyzable_paper_ids,
    }
