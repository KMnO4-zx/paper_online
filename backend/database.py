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
