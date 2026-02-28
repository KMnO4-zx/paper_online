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

    return result.data[0]


def save_paper(paper_info: dict, llm_response: str = None):
    if not supabase:
        return

    data = {
        "id": paper_info["id"],
        "title": paper_info.get("title"),
        "abstract": paper_info.get("abstract"),
        "keywords": paper_info.get("keywords", []),
        "pdf": paper_info.get("pdf"),
        "llm_response": llm_response
    }

    supabase.table("papers").upsert(data).execute()


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
