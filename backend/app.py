import asyncio
import math
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from pydantic import BaseModel

from llm import SiliconflowLLM, OpenRouterLLM
from utils import reader, get_openreview_info, ReaderError, OpenReviewError
from database import get_paper, save_paper, update_llm_response, get_chat_sessions, create_chat_session, get_chat_messages, save_chat_message, delete_chat_session, delete_last_chat_message_pair, get_conference_papers, search_all_papers
from chat import ChatSession

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = OpenRouterLLM()
chat_sessions: dict[str, ChatSession] = {}

# 在线用户追踪
online_users: dict[str, datetime] = {}
ONLINE_TIMEOUT = 30


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str


@app.post("/online/heartbeat")
async def heartbeat(request: dict):
    user_id = request.get("user_id")
    if user_id:
        online_users[user_id] = datetime.now()
    return {"status": "ok"}


@app.get("/online/count")
async def get_online_count():
    now = datetime.now()
    timeout_threshold = now - timedelta(seconds=ONLINE_TIMEOUT)
    active_users = {uid: ts for uid, ts in online_users.items() if ts > timeout_threshold}
    online_users.clear()
    online_users.update(active_users)
    return {"count": len(online_users)}


def get_or_fetch_paper_info(paper_id: str) -> dict:
    """Get paper from database, or fetch from OpenReview if not exists."""
    cached = get_paper(paper_id)
    if cached:
        return cached

    # Fetch from OpenReview and save basic info
    paper_info = get_openreview_info(paper_id)
    if not paper_info:
        raise OpenReviewError("Paper not found")

    save_paper(paper_info, llm_response=None)
    return paper_info


@app.get("/paper/{paper_id}/info")
async def get_paper_info(paper_id: str):
    """获取论文基本信息"""
    try:
        paper_info = get_or_fetch_paper_info(paper_id)
    except OpenReviewError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not paper_info:
        raise HTTPException(status_code=404, detail="Paper not found")

    return paper_info


@app.get("/paper/{paper_id}")
async def get_paper_analysis(paper_id: str, reanalyze: bool = False):
    async def generate():
        # Ensure paper exists in database
        yield {"event": "status", "data": "正在获取论文信息..."}
        try:
            paper_info = await asyncio.to_thread(get_or_fetch_paper_info, paper_id)
        except OpenReviewError as e:
            yield {"event": "error", "data": str(e)}
            return

        # Check if we can return cached analysis
        if not reanalyze and paper_info.get("llm_response"):
            yield {"data": paper_info["llm_response"]}
            yield {"event": "done", "data": ""}
            return

        # Perform AI analysis
        yield {"event": "status", "data": "正在读取 PDF 内容..."}
        try:
            paper_content = await asyncio.to_thread(reader, paper_info["pdf"])
        except ReaderError as e:
            yield {"event": "error", "data": str(e)}
            return

        yield {"event": "status", "data": "正在分析论文..."}

        user_prompt = f"以下是论文内容：\n{paper_content}"

        full_response = []
        async for chunk in llm.get_response_stream(user_prompt):
            full_response.append(chunk)
            yield {"data": chunk}

        update_llm_response(paper_id, "".join(full_response))
        yield {"event": "done", "data": ""}

    return EventSourceResponse(generate())


@app.post("/paper/{paper_id}/chat")
async def chat_with_paper(paper_id: str, req: ChatRequest):
    session = chat_sessions.get(req.session_id)
    is_new_session = False

    if not session:
        try:
            paper_info = await asyncio.to_thread(get_or_fetch_paper_info, paper_id)
        except OpenReviewError as e:
            raise HTTPException(status_code=502, detail=str(e))

        context_parts = []
        if paper_info.get("pdf"):
            paper_content = await asyncio.to_thread(reader, paper_info["pdf"])
            context_parts.append(f"论文全文：\n{paper_content}")
        if paper_info.get("llm_response"):
            context_parts.append(f"论文分析：\n{paper_info['llm_response']}")

        history_rows = get_chat_messages(req.session_id)
        if history_rows:
            history = [{"role": r["role"], "content": r["content"]} for r in history_rows]
        else:
            history = None
            is_new_session = True

        session = ChatSession(llm, context="\n\n".join(context_parts), history=history)
        chat_sessions[req.session_id] = session

    async def generate():
        if is_new_session:
            create_chat_session(req.session_id, req.user_id, paper_id, req.message[:50])

        chunks = []
        async for chunk in session.send_stream(req.message):
            chunks.append(chunk)
            yield {"data": chunk}

        # Persist messages
        save_chat_message(req.session_id, "user", req.message)
        save_chat_message(req.session_id, "assistant", "".join(chunks))

        yield {"event": "done", "data": ""}

    return EventSourceResponse(generate())


@app.get("/paper/{paper_id}/chat/sessions")
async def list_chat_sessions(paper_id: str, user_id: str):
    return get_chat_sessions(user_id, paper_id)


@app.get("/chat/{session_id}/messages")
async def list_chat_messages(session_id: str):
    return get_chat_messages(session_id)


@app.delete("/chat/{session_id}")
async def delete_session(session_id: str):
    chat_sessions.pop(session_id, None)
    delete_chat_session(session_id)
    return {"ok": True}


@app.post("/paper/{paper_id}/chat/regenerate")
async def regenerate_chat(paper_id: str, req: ChatRequest):
    """Delete last message pair, then re-send the user message."""
    session = chat_sessions.get(req.session_id)
    if session and len(session.history) >= 2:
        session.history = session.history[:-2]
    else:
        chat_sessions.pop(req.session_id, None)
        session = None

    delete_last_chat_message_pair(req.session_id)

    if not session:
        try:
            paper_info = await asyncio.to_thread(get_or_fetch_paper_info, paper_id)
        except OpenReviewError as e:
            raise HTTPException(status_code=502, detail=str(e))

        context_parts = []
        if paper_info.get("pdf"):
            paper_content = await asyncio.to_thread(reader, paper_info["pdf"])
            context_parts.append(f"论文全文：\n{paper_content}")
        if paper_info.get("llm_response"):
            context_parts.append(f"论文分析：\n{paper_info['llm_response']}")
        history_rows = get_chat_messages(req.session_id)
        history = [{"role": r["role"], "content": r["content"]} for r in history_rows] if history_rows else None
        session = ChatSession(llm, context="\n\n".join(context_parts), history=history)
        chat_sessions[req.session_id] = session

    async def generate():
        chunks = []
        async for chunk in session.send_stream(req.message):
            chunks.append(chunk)
            yield {"data": chunk}

        save_chat_message(req.session_id, "user", req.message)
        save_chat_message(req.session_id, "assistant", "".join(chunks))

        yield {"event": "done", "data": ""}

    return EventSourceResponse(generate())


@app.get("/conference/{venue}/papers")
async def get_conference_papers_endpoint(
    venue: str,
    page: int = 1,
    limit: int = 8,
    search: str = "",
    search_title: bool = True,
    search_abstract: bool = True,
    search_keywords: bool = True
):
    venue_map = {"neurips_2025": "NeurIPS 2025", "iclr_2026": "ICLR 2026", "icml_2025": "ICML 2025"}
    venue_name = venue_map.get(venue)
    if not venue_name:
        raise HTTPException(status_code=404, detail="Conference not found")

    offset = (page - 1) * limit
    papers, total = get_conference_papers(
        venue_name, offset, limit,
        search if search else None,
        search_title, search_abstract, search_keywords
    )

    return {
        "papers": papers,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if total > 0 else 1
    }


@app.get("/search/papers")
async def search_all_papers_endpoint(
    page: int = 1,
    limit: int = 8,
    search: str = "",
    search_title: bool = True,
    search_abstract: bool = True,
    search_keywords: bool = True
):
    offset = (page - 1) * limit
    papers, total = search_all_papers(
        offset, limit,
        search if search else None,
        search_title, search_abstract, search_keywords
    )

    return {
        "papers": papers,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if total > 0 else 1
    }


# 静态文件服务
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
IMAGES_DIR = Path(__file__).parent.parent / "images"

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")
