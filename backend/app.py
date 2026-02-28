import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from pydantic import BaseModel

from llm import SiliconflowLLM, OpenRouterLLM
from utils import reader, get_openreview_info, ReaderError, OpenReviewError
from database import get_paper, save_paper, update_llm_response, get_chat_sessions, create_chat_session, get_chat_messages, save_chat_message, delete_chat_session, delete_last_chat_message_pair
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


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str


@app.get("/paper/{paper_id}/info")
async def get_paper_info(paper_id: str):
    """获取论文基本信息"""
    try:
        paper_info = get_openreview_info(paper_id)
    except OpenReviewError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not paper_info:
        raise HTTPException(status_code=404, detail="Paper not found")

    return paper_info


@app.get("/paper/{paper_id}")
async def get_paper_analysis(paper_id: str, reanalyze: bool = False):
    # Check cache first
    cached = get_paper(paper_id)
    if not reanalyze and cached and cached.get("llm_response"):
        async def cached_stream():
            yield {"data": cached["llm_response"]}
        return EventSourceResponse(cached_stream())

    async def generate():
        # 发送状态消息
        yield {"event": "status", "data": "正在获取论文信息..."}

        # Fetch paper info from OpenReview (异步执行)
        try:
            paper_info = await asyncio.to_thread(get_openreview_info, paper_id)
        except OpenReviewError as e:
            yield {"event": "error", "data": str(e)}
            return

        if not paper_info:
            yield {"event": "error", "data": "论文未找到"}
            return

        yield {"event": "status", "data": "正在读取 PDF 内容..."}

        # Get PDF content via Jina Reader (异步执行)
        try:
            paper_content = await asyncio.to_thread(reader, paper_info["pdf"])
        except ReaderError as e:
            yield {"event": "error", "data": str(e)}
            return

        yield {"event": "status", "data": "正在分析论文..."}

        user_prompt = f"以下是论文内容：\n{paper_content}"

        # Stream LLM response using thread-safe queue
        import queue as thread_queue
        import threading
        q = thread_queue.Queue()

        def run_llm():
            try:
                for chunk in llm.get_response_stream(user_prompt):
                    q.put(chunk)
            finally:
                q.put(None)

        thread = threading.Thread(target=run_llm)
        thread.start()

        full_response = []
        while True:
            try:
                chunk = q.get(timeout=0.05)
            except thread_queue.Empty:
                await asyncio.sleep(0.01)
                continue
            if chunk is None:
                break
            full_response.append(chunk)
            yield {"data": chunk}

        thread.join()

        # Save to database after streaming completes
        response_text = "".join(full_response)
        if cached:
            update_llm_response(paper_id, response_text)
        else:
            save_paper(paper_info, response_text)

    return EventSourceResponse(generate())


@app.post("/paper/{paper_id}/chat")
async def chat_with_paper(paper_id: str, req: ChatRequest):
    session = chat_sessions.get(req.session_id)
    is_new_session = False

    if not session:
        cached = get_paper(paper_id)
        if not cached:
            raise HTTPException(status_code=404, detail="Paper not found")

        context_parts = []
        if cached.get("pdf"):
            paper_content = await asyncio.to_thread(reader, cached["pdf"])
            context_parts.append(f"论文全文：\n{paper_content}")
        if cached.get("llm_response"):
            context_parts.append(f"论文分析：\n{cached['llm_response']}")

        # Try loading history from DB
        history_rows = get_chat_messages(req.session_id)
        if history_rows:
            history = [{"role": r["role"], "content": r["content"]} for r in history_rows]
        else:
            history = None
            is_new_session = True

        session = ChatSession(llm, context="\n\n".join(context_parts), history=history)
        chat_sessions[req.session_id] = session

    import queue as thread_queue
    import threading

    q = thread_queue.Queue()

    def run_chat():
        try:
            for chunk in session.send_stream(req.message):
                q.put(chunk)
        finally:
            q.put(None)

    async def generate():
        if is_new_session:
            create_chat_session(req.session_id, req.user_id, paper_id, req.message[:50])

        thread = threading.Thread(target=run_chat)
        thread.start()

        chunks = []
        while True:
            try:
                chunk = q.get(timeout=0.05)
            except thread_queue.Empty:
                await asyncio.sleep(0.01)
                continue
            if chunk is None:
                break
            chunks.append(chunk)
            yield {"data": chunk}

        thread.join()

        # Persist messages
        save_chat_message(req.session_id, "user", req.message)
        save_chat_message(req.session_id, "assistant", "".join(chunks))

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
        cached = get_paper(paper_id)
        if not cached:
            raise HTTPException(status_code=404, detail="Paper not found")
        context_parts = []
        if cached.get("pdf"):
            paper_content = await asyncio.to_thread(reader, cached["pdf"])
            context_parts.append(f"论文全文：\n{paper_content}")
        if cached.get("llm_response"):
            context_parts.append(f"论文分析：\n{cached['llm_response']}")
        history_rows = get_chat_messages(req.session_id)
        history = [{"role": r["role"], "content": r["content"]} for r in history_rows] if history_rows else None
        session = ChatSession(llm, context="\n\n".join(context_parts), history=history)
        chat_sessions[req.session_id] = session

    import queue as thread_queue
    import threading
    q = thread_queue.Queue()

    def run_chat():
        try:
            for chunk in session.send_stream(req.message):
                q.put(chunk)
        finally:
            q.put(None)

    async def generate():
        thread = threading.Thread(target=run_chat)
        thread.start()
        chunks = []
        while True:
            try:
                chunk = q.get(timeout=0.05)
            except thread_queue.Empty:
                await asyncio.sleep(0.01)
                continue
            if chunk is None:
                break
            chunks.append(chunk)
            yield {"data": chunk}
        thread.join()
        save_chat_message(req.session_id, "user", req.message)
        save_chat_message(req.session_id, "assistant", "".join(chunks))

    return EventSourceResponse(generate())


# 静态文件服务
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")
