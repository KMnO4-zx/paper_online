#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

import psycopg
import tiktoken
from psycopg.rows import dict_row

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "backend"))

from config import settings
from code_availability import classify_code_availability_from_text
from llm import ManagedLLM
from utils import ReaderError, get_or_cache_paper_content, normalize_paper_pdf_url

DATABASE_URL = settings.database.url
TOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")
logging.getLogger("httpx").setLevel(logging.WARNING)


def truncate_to_tokens_or_chars(text: str, max_tokens: int, max_chars: int) -> str:
    token_ids = TOKEN_ENCODING.encode(text, disallowed_special=())
    if len(token_ids) <= max_tokens:
        return text[:max_chars]
    return TOKEN_ENCODING.decode(token_ids[:max_tokens])[:max_chars]


def fetch_random_papers(limit: int, source: str, seed: float | None) -> list[dict[str, Any]]:
    if not DATABASE_URL:
        raise RuntimeError("database.url not found in config.yaml")

    where_parts = ["COALESCE(title, '') <> ''"]
    if source == "llm_response":
        where_parts.append("llm_response IS NOT NULL")
        where_parts.append("BTRIM(llm_response) <> ''")
    if source == "paper_content":
        where_parts.append("pdf IS NOT NULL")
        where_parts.append("BTRIM(pdf) <> ''")

    where_clause = " AND ".join(where_parts)
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            if seed is not None:
                cur.execute("SELECT setseed(%s)", (seed,))
            cur.execute(
                f"""
                SELECT id, title, venue, pdf, llm_response
                FROM papers
                WHERE {where_clause}
                ORDER BY RANDOM()
                LIMIT %s
                """,
                (limit,),
            )
            return list(cur.fetchall())


def build_input_text(paper: dict[str, Any], source: str, max_tokens: int, max_chars: int) -> tuple[str, str | None]:
    if source == "llm_response":
        text = str(paper.get("llm_response") or "")
        return truncate_to_tokens_or_chars(text, max_tokens, max_chars), None

    paper_id = str(paper["id"])
    pdf_url = normalize_paper_pdf_url(paper_id, paper.get("pdf"))
    if not pdf_url:
        raise ReaderError("paper has no usable PDF URL")

    content = get_or_cache_paper_content(paper_id, pdf_url)
    return truncate_to_tokens_or_chars(content, max_tokens, max_chars), pdf_url


async def classify_paper(
    llm: ManagedLLM,
    paper: dict[str, Any],
    source_text: str,
    source: str,
) -> dict[str, Any]:
    return await classify_code_availability_from_text(
        llm,
        paper,
        source_text,
        source=source,
    )


async def main() -> int:
    parser = argparse.ArgumentParser(description="Test code availability classification on random papers.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--source",
        choices=["llm_response", "paper_content"],
        default="llm_response",
        help="llm_response is cheap; paper_content reads PDF/cache and keeps only the first token window.",
    )
    parser.add_argument("--max-tokens", type=int, default=1000)
    parser.add_argument("--max-chars", type=int, default=5000)
    parser.add_argument("--seed", type=float, default=None, help="PostgreSQL setseed value between -1 and 1.")
    args = parser.parse_args()

    llm = ManagedLLM()
    if not llm.is_configured():
        raise RuntimeError("No active LLM provider is configured")

    papers = fetch_random_papers(max(args.limit, 1), args.source, args.seed)
    if not papers:
        print(f"No papers found for source={args.source}")
        return 1

    for index, paper in enumerate(papers, start=1):
        print(f"\n[{index}/{len(papers)}] {paper['id']} | {paper.get('title') or ''}")
        try:
            source_text, pdf_url = build_input_text(paper, args.source, args.max_tokens, args.max_chars)
            result = await classify_paper(llm, paper, source_text, args.source)
        except Exception as exc:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2))
            continue

        payload = {
            "paper_id": paper["id"],
            "title": paper.get("title"),
            "venue": paper.get("venue"),
            "source": args.source,
            "text_chars": len(source_text),
            "pdf_url": pdf_url if args.source == "paper_content" else None,
            "result": result,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
