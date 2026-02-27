import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from llm import SiliconflowLLM, OpenRouterLLM
from utils import reader, get_openreview_info, ReaderError, OpenReviewError
from database import get_paper, save_paper, update_llm_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = OpenRouterLLM()


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
async def get_paper_analysis(paper_id: str):
    # Check cache first
    cached = get_paper(paper_id)
    if cached and cached.get("llm_response"):
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


# 静态文件服务
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")
