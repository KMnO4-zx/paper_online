import os
from supabase import create_client

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


def get_paper(paper_id: str) -> dict | None:
    if not supabase:
        return None

    result = supabase.table("papers").select("*").eq("id", paper_id).execute()

    if not result.data:
        return None

    paper = result.data[0]

    # Fetch authors
    authors_result = supabase.table("authors").select("author_name").eq("paper_id", paper_id).order("author_order").execute()
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
        "llm_response": llm_response
    }

    supabase.table("papers").upsert(data).execute()

    # Save authors
    authors = paper_info.get("authors", [])
    if authors:
        supabase.table("authors").delete().eq("paper_id", paper_info["id"]).execute()
        for i, author in enumerate(authors):
            supabase.table("authors").insert({
                "paper_id": paper_info["id"],
                "author_name": author,
                "author_order": i
            }).execute()

    # Save keywords
    keywords = paper_info.get("keywords", [])
    if keywords:
        supabase.table("keywords").delete().eq("paper_id", paper_info["id"]).execute()
        for keyword in keywords:
            supabase.table("keywords").insert({
                "paper_id": paper_info["id"],
                "keyword": keyword
            }).execute()


def update_llm_response(paper_id: str, response: str):
    if not supabase:
        return

    supabase.table("papers").update({"llm_response": response}).eq("id", paper_id).execute()


def get_chat_sessions(user_id: str, paper_id: str) -> list:
    if not supabase:
        return []
    result = supabase.table("chat_sessions").select("*").eq("user_id", user_id).eq("paper_id", paper_id).order("created_at", desc=True).execute()
    return result.data or []


def create_chat_session(session_id: str, user_id: str, paper_id: str, title: str):
    if not supabase:
        return
    supabase.table("chat_sessions").insert({
        "id": session_id, "user_id": user_id, "paper_id": paper_id, "title": title
    }).execute()


def get_chat_messages(session_id: str) -> list:
    if not supabase:
        return []
    result = supabase.table("chat_messages").select("role, content, created_at").eq("session_id", session_id).order("created_at").execute()
    return result.data or []


def save_chat_message(session_id: str, role: str, content: str):
    if not supabase:
        return
    supabase.table("chat_messages").insert({
        "session_id": session_id, "role": role, "content": content
    }).execute()


def delete_chat_session(session_id: str):
    if not supabase:
        return
    supabase.table("chat_messages").delete().eq("session_id", session_id).execute()
    supabase.table("chat_sessions").delete().eq("id", session_id).execute()


def delete_last_chat_message_pair(session_id: str):
    """Delete the last user+assistant message pair from a session."""
    if not supabase:
        return
    rows = supabase.table("chat_messages").select("id").eq("session_id", session_id).order("created_at", desc=True).limit(2).execute()
    for r in (rows.data or []):
        supabase.table("chat_messages").delete().eq("id", r["id"]).execute()


def get_conference_papers(venue: str, offset: int, limit: int, search: str = None):
    if not supabase:
        return [], 0

    query = supabase.table("papers").select("*", count="exact").ilike("venue", f"{venue}%")

    if search:
        # Search in keywords table
        keywords_result = supabase.table("keywords").select("paper_id").ilike("keyword", f"%{search}%").execute()
        paper_ids_from_keywords = list(set([k["paper_id"] for k in keywords_result.data]))

        # Search in title and abstract using OR logic
        if paper_ids_from_keywords:
            query = query.or_(f"title.ilike.%{search}%,abstract.ilike.%{search}%,id.in.({','.join(paper_ids_from_keywords)})")
        else:
            query = query.or_(f"title.ilike.%{search}%,abstract.ilike.%{search}%")

    result = query.range(offset, offset + limit - 1).execute()

    # Batch fetch all keywords in one query
    if result.data:
        paper_ids = [p["id"] for p in result.data]
        keywords_result = supabase.table("keywords").select("paper_id, keyword").in_("paper_id", paper_ids).execute()

        # Group keywords by paper_id
        keywords_by_paper = {}
        for k in keywords_result.data:
            if k["paper_id"] not in keywords_by_paper:
                keywords_by_paper[k["paper_id"]] = []
            keywords_by_paper[k["paper_id"]].append(k["keyword"])

        # Attach keywords to papers
        for paper in result.data:
            paper["keywords"] = keywords_by_paper.get(paper["id"], [])

    return result.data, result.count
