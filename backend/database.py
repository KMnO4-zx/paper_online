import logging
import os
import time
from contextlib import contextmanager
from typing import Callable, Iterator, TypeVar

import psycopg
from dotenv import find_dotenv, load_dotenv
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from utils import get_openreview_pdf_url, normalize_paper_pdf_url

load_dotenv(find_dotenv())

DATABASE_URL = os.getenv("DATABASE_URL")

logger = logging.getLogger(__name__)
T = TypeVar("T")

# Cache for conference/search results
_conference_cache = {}
_cache_timestamp = {}
_CACHE_TTL_SECONDS = 86400


class DatabaseError(Exception):
    """Raised when database access fails after retries."""


def _run_with_retry(
    operation: Callable[[], T],
    context: str,
    retries: int = 3,
    delay: float = 1.0,
) -> T:
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Database operation failed for %s (attempt %s/%s): %s",
                context,
                attempt + 1,
                retries,
                exc,
            )
            if attempt < retries - 1:
                time.sleep(delay)

    raise DatabaseError(f"Database operation failed for {context}") from last_error


@contextmanager
def _get_connection() -> Iterator[psycopg.Connection]:
    if not DATABASE_URL:
        raise DatabaseError("DATABASE_URL is not configured")

    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def _fetch_keywords_for_papers(conn: psycopg.Connection, paper_ids: list[str]) -> dict[str, list[str]]:
    if not paper_ids:
        return {}

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT paper_id, keyword
            FROM keywords
            WHERE paper_id = ANY(%s)
            ORDER BY id
            """,
            (paper_ids,),
        )
        rows = cur.fetchall()

    keywords_by_paper: dict[str, list[str]] = {}
    for row in rows:
        keywords_by_paper.setdefault(row["paper_id"], []).append(row["keyword"])
    return keywords_by_paper


def get_paper(paper_id: str) -> dict | None:
    if not DATABASE_URL:
        return None

    def operation() -> dict | None:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM papers WHERE id = %s", (paper_id,))
                paper = cur.fetchone()
                if not paper:
                    return None

                cur.execute(
                    """
                    SELECT author_name
                    FROM authors
                    WHERE paper_id = %s
                    ORDER BY author_order
                    """,
                    (paper_id,),
                )
                paper["authors"] = [row["author_name"] for row in cur.fetchall()]

                cur.execute(
                    """
                    SELECT keyword
                    FROM keywords
                    WHERE paper_id = %s
                    ORDER BY id
                    """,
                    (paper_id,),
                )
                paper["keywords"] = [row["keyword"] for row in cur.fetchall()]
                paper["pdf"] = normalize_paper_pdf_url(paper_id, paper.get("pdf")) or get_openreview_pdf_url(paper_id)
                return paper

    return _run_with_retry(operation, f"get_paper:{paper_id}")


def save_paper(paper_info: dict, llm_response: str = None):
    if not DATABASE_URL:
        return

    def operation() -> None:
        normalized_pdf = normalize_paper_pdf_url(paper_info["id"], paper_info.get("pdf"))
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO papers (
                        id,
                        title,
                        abstract,
                        keywords,
                        pdf,
                        venue,
                        primary_area,
                        llm_response
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        abstract = EXCLUDED.abstract,
                        keywords = EXCLUDED.keywords,
                        pdf = EXCLUDED.pdf,
                        venue = EXCLUDED.venue,
                        primary_area = EXCLUDED.primary_area,
                        llm_response = EXCLUDED.llm_response
                    """,
                    (
                        paper_info["id"],
                        paper_info.get("title"),
                        paper_info.get("abstract"),
                        Jsonb(paper_info.get("keywords", [])),
                        normalized_pdf,
                        paper_info.get("venue"),
                        paper_info.get("primary_area"),
                        llm_response,
                    ),
                )

                cur.execute("DELETE FROM authors WHERE paper_id = %s", (paper_info["id"],))
                authors = paper_info.get("authors", [])
                if authors:
                    cur.executemany(
                        """
                        INSERT INTO authors (paper_id, author_name, author_order)
                        VALUES (%s, %s, %s)
                        """,
                        [
                            (paper_info["id"], author, index)
                            for index, author in enumerate(authors)
                        ],
                    )

                cur.execute("DELETE FROM keywords WHERE paper_id = %s", (paper_info["id"],))
                keywords = paper_info.get("keywords", [])
                if keywords:
                    cur.executemany(
                        """
                        INSERT INTO keywords (paper_id, keyword)
                        VALUES (%s, %s)
                        """,
                        [(paper_info["id"], keyword) for keyword in keywords],
                    )

            conn.commit()

    _run_with_retry(operation, f"save_paper:{paper_info['id']}")


def update_llm_response(paper_id: str, response: str):
    if not DATABASE_URL:
        return

    def operation() -> None:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE papers
                    SET llm_response = %s
                    WHERE id = %s
                    """,
                    (response, paper_id),
                )
            conn.commit()

    _run_with_retry(operation, f"update_llm_response:{paper_id}")


def get_chat_sessions(user_id: str, paper_id: str) -> list:
    if not DATABASE_URL:
        return []

    def operation() -> list:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM chat_sessions
                    WHERE user_id = %s AND paper_id = %s
                    ORDER BY created_at DESC
                    """,
                    (user_id, paper_id),
                )
                return cur.fetchall()

    return _run_with_retry(operation, f"get_chat_sessions:{user_id}:{paper_id}")


def create_chat_session(session_id: str, user_id: str, paper_id: str, title: str):
    if not DATABASE_URL:
        return

    def operation() -> None:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_sessions (id, user_id, paper_id, title)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (session_id, user_id, paper_id, title),
                )
            conn.commit()

    _run_with_retry(operation, f"create_chat_session:{session_id}")


def get_chat_messages(session_id: str) -> list:
    if not DATABASE_URL:
        return []

    def operation() -> list:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content, created_at
                    FROM chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at
                    """,
                    (session_id,),
                )
                return cur.fetchall()

    return _run_with_retry(operation, f"get_chat_messages:{session_id}")


def save_chat_message(session_id: str, role: str, content: str):
    if not DATABASE_URL:
        return

    def operation() -> None:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_messages (session_id, role, content)
                    VALUES (%s, %s, %s)
                    """,
                    (session_id, role, content),
                )
            conn.commit()

    _run_with_retry(operation, f"save_chat_message:{session_id}:{role}")


def delete_chat_session(session_id: str):
    if not DATABASE_URL:
        return

    def operation() -> None:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chat_messages WHERE session_id = %s", (session_id,))
                cur.execute("DELETE FROM chat_sessions WHERE id = %s", (session_id,))
            conn.commit()

    _run_with_retry(operation, f"delete_chat_session:{session_id}")


def delete_last_chat_message_pair(session_id: str):
    """Delete the last user+assistant message pair from a session."""
    if not DATABASE_URL:
        return

    def operation() -> None:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id
                    FROM chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT 2
                    """,
                    (session_id,),
                )
                rows = cur.fetchall()
                if rows:
                    cur.execute(
                        "DELETE FROM chat_messages WHERE id = ANY(%s)",
                        ([row["id"] for row in rows],),
                    )
            conn.commit()

    _run_with_retry(operation, f"delete_last_chat_message_pair:{session_id}")


def _build_cache_key(
    venue_prefix: str | None,
    offset: int,
    limit: int,
    search: str | None,
    search_title: bool,
    search_abstract: bool,
    search_keywords: bool,
) -> str:
    scope = venue_prefix if venue_prefix is not None else "all"
    return (
        f"{scope}:{offset}:{limit}:{search or ''}:"
        f"{search_title}:{search_abstract}:{search_keywords}"
    )


def _get_cached_result(cache_key: str):
    current_time = time.time()
    if cache_key in _conference_cache and (
        current_time - _cache_timestamp.get(cache_key, 0)
    ) < _CACHE_TTL_SECONDS:
        return _conference_cache[cache_key]
    return None


def _set_cached_result(cache_key: str, papers: list, total: int):
    _conference_cache[cache_key] = (papers, total)
    _cache_timestamp[cache_key] = time.time()


def _load_keywords_for_papers(papers: list[dict]) -> tuple[list[dict], bool]:
    if not papers:
        return papers, True

    paper_ids = [paper["id"] for paper in papers]

    try:
        with _get_connection() as conn:
            keywords_by_paper = _fetch_keywords_for_papers(conn, paper_ids)
    except Exception:
        for paper in papers:
            paper["keywords"] = []
        return papers, False

    for paper in papers:
        paper["keywords"] = keywords_by_paper.get(paper["id"], [])

    return papers, True


def _search_papers_via_rpc(
    venue_prefix: str | None,
    offset: int,
    limit: int,
    search: str | None,
    search_title: bool,
    search_abstract: bool,
    search_keywords: bool,
) -> tuple[list[dict], int]:
    def operation() -> tuple[list[dict], int]:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM search_papers_optimized(%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        search,
                        venue_prefix,
                        search_title,
                        search_abstract,
                        search_keywords,
                        limit,
                        offset,
                    ),
                )
                papers = cur.fetchall()
                papers, _ = _load_keywords_for_papers(papers)

                cur.execute(
                    """
                    SELECT count_papers_optimized(%s, %s, %s, %s, %s) AS total
                    """,
                    (
                        search,
                        venue_prefix,
                        search_title,
                        search_abstract,
                        search_keywords,
                    ),
                )
                row = cur.fetchone()
                total = int(row["total"] or 0)

        return papers, total

    return _run_with_retry(operation, "search_papers_via_rpc")


def _paper_type_priority(paper: dict) -> int:
    venue_value = (paper.get("venue") or "").lower()
    if "oral" in venue_value:
        return 1
    if "spotlight" in venue_value:
        return 2
    if "poster" in venue_value:
        return 3
    return 4


def _normalized_title(paper: dict) -> str:
    return (paper.get("title") or "").casefold()


def _stable_paper_sort_key(paper: dict) -> tuple[int, str, str]:
    return (
        _paper_type_priority(paper),
        _normalized_title(paper),
        paper.get("id") or "",
    )


def _legacy_search_rank_score(
    paper: dict,
    normalized_search: str,
    search_title: bool,
    search_abstract: bool,
    matched_keyword_paper_ids: set[str],
) -> int:
    score = 0
    title = (paper.get("title") or "").casefold()
    abstract = (paper.get("abstract") or "").casefold()
    paper_id = paper.get("id") or ""

    if search_title and normalized_search in title:
        score += 3
    if search_abstract and normalized_search in abstract:
        score += 2
    if paper_id in matched_keyword_paper_ids:
        score += 1

    return score


def _search_papers_legacy(
    venue_prefix: str | None,
    offset: int,
    limit: int,
    search: str | None,
    search_title: bool,
    search_abstract: bool,
    search_keywords: bool,
) -> tuple[list[dict], int]:
    normalized_search = (search or "").casefold()
    matched_keyword_paper_ids: set[str] = set()

    with _get_connection() as conn:
        with conn.cursor() as cur:
            if search and search_keywords:
                cur.execute(
                    """
                    SELECT DISTINCT paper_id
                    FROM keywords
                    WHERE keyword ILIKE %s
                    """,
                    (f"%{search}%",),
                )
                matched_keyword_paper_ids = {
                    row["paper_id"] for row in cur.fetchall()
                }

            query = "SELECT * FROM papers"
            params: list[object] = []
            if venue_prefix:
                query += " WHERE venue ILIKE %s"
                params.append(f"{venue_prefix}%")
            cur.execute(query, params)
            all_papers = cur.fetchall()

    if search:
        filtered_papers = []
        for paper in all_papers:
            title = (paper.get("title") or "").casefold()
            abstract = (paper.get("abstract") or "").casefold()
            paper_id = paper.get("id") or ""

            if (
                (search_title and normalized_search in title)
                or (search_abstract and normalized_search in abstract)
                or (paper_id in matched_keyword_paper_ids)
            ):
                filtered_papers.append(paper)
        all_papers = filtered_papers

    if search:
        sorted_papers = sorted(
            all_papers,
            key=lambda paper: (
                -_legacy_search_rank_score(
                    paper,
                    normalized_search,
                    search_title,
                    search_abstract,
                    matched_keyword_paper_ids,
                ),
                *_stable_paper_sort_key(paper),
            ),
        )
    else:
        sorted_papers = sorted(all_papers, key=_stable_paper_sort_key)

    paginated_papers = sorted_papers[offset : offset + limit]
    paginated_papers, _ = _load_keywords_for_papers(paginated_papers)
    return paginated_papers, len(sorted_papers)


def _search_papers(
    venue_prefix: str | None,
    offset: int,
    limit: int,
    search: str | None,
    search_title: bool,
    search_abstract: bool,
    search_keywords: bool,
) -> tuple[list[dict], int]:
    if not DATABASE_URL:
        return [], 0

    if search and not (search_title or search_abstract or search_keywords):
        return [], 0

    cache_key = _build_cache_key(
        venue_prefix, offset, limit, search, search_title, search_abstract, search_keywords
    )
    cached_result = _get_cached_result(cache_key)
    if cached_result is not None:
        return cached_result

    try:
        papers, total = _search_papers_via_rpc(
            venue_prefix,
            offset,
            limit,
            search,
            search_title,
            search_abstract,
            search_keywords,
        )
    except Exception as exc:
        logger.warning(
            "Falling back to legacy paper search for venue_prefix=%r search=%r: %s",
            venue_prefix,
            search,
            exc,
        )
        papers, total = _search_papers_legacy(
            venue_prefix,
            offset,
            limit,
            search,
            search_title,
            search_abstract,
            search_keywords,
        )

    _set_cached_result(cache_key, papers, total)
    return papers, total


def get_conference_papers(
    venue: str,
    offset: int,
    limit: int,
    search: str = None,
    search_title: bool = True,
    search_abstract: bool = True,
    search_keywords: bool = True,
):
    return _search_papers(
        venue,
        offset,
        limit,
        search,
        search_title,
        search_abstract,
        search_keywords,
    )


def search_all_papers(
    offset: int,
    limit: int,
    search: str = None,
    search_title: bool = True,
    search_abstract: bool = True,
    search_keywords: bool = True,
):
    return _search_papers(
        None,
        offset,
        limit,
        search,
        search_title,
        search_abstract,
        search_keywords,
    )


def get_unanalyzed_papers(limit: int = 10) -> list:
    """获取未分析的论文（llm_response IS NULL）"""
    if not DATABASE_URL:
        return []

    def operation() -> list:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, venue
                    FROM papers
                    WHERE llm_response IS NULL
                    LIMIT %s
                    """,
                    (limit,),
                )
                return cur.fetchall()

    return _run_with_retry(operation, f"get_unanalyzed_papers:{limit}")
