import logging
import os
import time

from supabase import create_client

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
logger = logging.getLogger(__name__)

# Cache for conference/search results
_conference_cache = {}
_cache_timestamp = {}
_CACHE_TTL_SECONDS = 86400


def get_paper(paper_id: str) -> dict | None:
    if not supabase:
        return None

    result = supabase.table("papers").select("*").eq("id", paper_id).execute()

    if not result.data:
        return None

    paper = result.data[0]

    # Fetch authors
    authors_result = (
        supabase.table("authors")
        .select("author_name")
        .eq("paper_id", paper_id)
        .order("author_order")
        .execute()
    )
    paper["authors"] = [a["author_name"] for a in (authors_result.data or [])]

    # Fetch keywords
    keywords_result = supabase.table("keywords").select("keyword").eq("paper_id", paper_id).execute()
    paper["keywords"] = [k["keyword"] for k in (keywords_result.data or [])]

    # Construct PDF URL
    paper["pdf"] = f"https://openreview.net/pdf?id={paper_id}"

    return paper


def save_paper(paper_info: dict, llm_response: str = None):
    if not supabase:
        return

    data = {
        "id": paper_info["id"],
        "title": paper_info.get("title"),
        "abstract": paper_info.get("abstract"),
        "venue": paper_info.get("venue"),
        "primary_area": paper_info.get("primary_area"),
        "llm_response": llm_response,
    }

    supabase.table("papers").upsert(data).execute()

    # Save authors
    authors = paper_info.get("authors", [])
    if authors:
        supabase.table("authors").delete().eq("paper_id", paper_info["id"]).execute()
        author_rows = [
            {"paper_id": paper_info["id"], "author_name": author, "author_order": i}
            for i, author in enumerate(authors)
        ]
        supabase.table("authors").insert(author_rows).execute()

    # Save keywords
    keywords = paper_info.get("keywords", [])
    if keywords:
        supabase.table("keywords").delete().eq("paper_id", paper_info["id"]).execute()
        keyword_rows = [
            {"paper_id": paper_info["id"], "keyword": keyword} for keyword in keywords
        ]
        supabase.table("keywords").insert(keyword_rows).execute()


def update_llm_response(paper_id: str, response: str):
    if not supabase:
        return

    supabase.table("papers").update({"llm_response": response}).eq("id", paper_id).execute()


def get_chat_sessions(user_id: str, paper_id: str) -> list:
    if not supabase:
        return []
    result = (
        supabase.table("chat_sessions")
        .select("*")
        .eq("user_id", user_id)
        .eq("paper_id", paper_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


def create_chat_session(session_id: str, user_id: str, paper_id: str, title: str):
    if not supabase:
        return
    supabase.table("chat_sessions").insert(
        {"id": session_id, "user_id": user_id, "paper_id": paper_id, "title": title}
    ).execute()


def get_chat_messages(session_id: str) -> list:
    if not supabase:
        return []
    result = (
        supabase.table("chat_messages")
        .select("role, content, created_at")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return result.data or []


def save_chat_message(session_id: str, role: str, content: str):
    if not supabase:
        return
    supabase.table("chat_messages").insert(
        {"session_id": session_id, "role": role, "content": content}
    ).execute()


def delete_chat_session(session_id: str):
    if not supabase:
        return
    supabase.table("chat_messages").delete().eq("session_id", session_id).execute()
    supabase.table("chat_sessions").delete().eq("id", session_id).execute()


def delete_last_chat_message_pair(session_id: str):
    """Delete the last user+assistant message pair from a session."""
    if not supabase:
        return
    rows = (
        supabase.table("chat_messages")
        .select("id")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(2)
        .execute()
    )
    for r in (rows.data or []):
        supabase.table("chat_messages").delete().eq("id", r["id"]).execute()


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

    paper_ids = [p["id"] for p in papers]

    for retry in range(3):
        try:
            keywords_result = (
                supabase.table("keywords")
                .select("paper_id, keyword")
                .in_("paper_id", paper_ids)
                .execute()
            )
            break
        except Exception:
            if retry == 2:
                for paper in papers:
                    paper["keywords"] = []
                return papers, False
            time.sleep(1)

    keywords_by_paper = {}
    for row in keywords_result.data or []:
        keywords_by_paper.setdefault(row["paper_id"], []).append(row["keyword"])

    for paper in papers:
        paper["keywords"] = keywords_by_paper.get(paper["id"], [])

    return papers, True


def _extract_count_value(data) -> int:
    if data is None:
        raise ValueError("RPC count response is empty")

    if isinstance(data, (int, float)):
        return int(data)

    if isinstance(data, str):
        return int(data)

    if isinstance(data, list):
        if not data:
            return 0
        first = data[0]
        if isinstance(first, (int, float)):
            return int(first)
        if isinstance(first, dict):
            if "count_papers_optimized" in first:
                return int(first["count_papers_optimized"])
            if len(first) == 1:
                return int(next(iter(first.values())))

    if isinstance(data, dict):
        if "count_papers_optimized" in data:
            return int(data["count_papers_optimized"])
        if len(data) == 1:
            return int(next(iter(data.values())))

    raise ValueError(f"Unsupported RPC count response shape: {type(data)!r}")


def _search_papers_via_rpc(
    venue_prefix: str | None,
    offset: int,
    limit: int,
    search: str | None,
    search_title: bool,
    search_abstract: bool,
    search_keywords: bool,
) -> tuple[list[dict], int]:
    params = {
        "search_term": search,
        "venue_prefix": venue_prefix,
        "search_title": search_title,
        "search_abstract": search_abstract,
        "search_keywords": search_keywords,
        "page_limit": limit,
        "page_offset": offset,
    }

    papers_result = supabase.rpc("search_papers_optimized", params).execute()
    count_result = supabase.rpc(
        "count_papers_optimized",
        {
            "search_term": search,
            "venue_prefix": venue_prefix,
            "search_title": search_title,
            "search_abstract": search_abstract,
            "search_keywords": search_keywords,
        },
    ).execute()

    papers = papers_result.data or []
    papers, _ = _load_keywords_for_papers(papers)
    total = _extract_count_value(count_result.data)
    return papers, total


def _paper_type_priority(paper: dict) -> int:
    venue_value = (paper.get("venue") or "").lower()
    if "oral" in venue_value:
        return 1
    if "spotlight" in venue_value:
        return 2
    if "poster" in venue_value:
        return 3
    return 4


def _search_papers_legacy(
    venue_prefix: str | None,
    offset: int,
    limit: int,
    search: str | None,
    search_title: bool,
    search_abstract: bool,
    search_keywords: bool,
) -> tuple[list[dict], int]:
    all_papers = []
    batch_size = 1000
    current_offset = 0

    while True:
        for retry in range(3):
            try:
                query = supabase.table("papers").select("*")
                if venue_prefix:
                    query = query.ilike("venue", f"{venue_prefix}%")

                if search:
                    conditions = []

                    if search_keywords:
                        keywords_result = (
                            supabase.table("keywords")
                            .select("paper_id")
                            .ilike("keyword", f"%{search}%")
                            .execute()
                        )
                        paper_ids_from_keywords = list(
                            {k["paper_id"] for k in (keywords_result.data or [])}
                        )
                        if paper_ids_from_keywords:
                            conditions.append(f"id.in.({','.join(paper_ids_from_keywords)})")

                    if search_title:
                        conditions.append(f"title.ilike.%{search}%")

                    if search_abstract:
                        conditions.append(f"abstract.ilike.%{search}%")

                    if not conditions:
                        return [], 0

                    if conditions:
                        query = query.or_(",".join(conditions))

                result = query.range(current_offset, current_offset + batch_size - 1).execute()
                break
            except Exception:
                if retry == 2:
                    raise
                time.sleep(1)

        if not result.data:
            break

        all_papers.extend(result.data)

        if len(result.data) < batch_size:
            break

        current_offset += batch_size

    sorted_papers = sorted(all_papers, key=_paper_type_priority)
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
    if not supabase:
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
    if not supabase:
        return []

    result = (
        supabase.table("papers")
        .select("id, title, venue")
        .is_("llm_response", "null")
        .limit(limit)
        .execute()
    )
    return result.data or []
