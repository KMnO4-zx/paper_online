import asyncio
import logging
from datetime import datetime, timezone
from analysis_context import build_analysis_prompt
from database import get_unanalyzed_papers, get_paper, update_llm_response
from markdown_utils import normalize_llm_markdown
from utils import get_or_cache_paper_content, ReaderError, truncate_content_for_llm

logger = logging.getLogger(__name__)

class BackgroundAnalyzer:
    def __init__(self, llm, check_interval: int = 3600):
        self.llm = llm
        self.check_interval = check_interval
        self.running = False
        self.current_paper_id = None
        self.last_run_started_at = None
        self.last_run_finished_at = None
        self.last_run_success_count = 0
        self.last_run_failed_count = 0
        self.last_run_error = None
        self.last_analyzed_paper_id = None
        self._wake_event = asyncio.Event()

    def status_snapshot(self) -> dict:
        return {
            "running": self.running,
            "check_interval_seconds": self.check_interval,
            "current_paper_id": self.current_paper_id,
            "last_run_started_at": self.last_run_started_at,
            "last_run_finished_at": self.last_run_finished_at,
            "last_run_success_count": self.last_run_success_count,
            "last_run_failed_count": self.last_run_failed_count,
            "last_run_error": self.last_run_error,
            "last_analyzed_paper_id": self.last_analyzed_paper_id,
        }

    def set_check_interval(self, check_interval: int) -> None:
        self.check_interval = check_interval
        self._wake_event.set()

    async def _sleep_until_next_check(self) -> None:
        self._wake_event.clear()
        try:
            await asyncio.wait_for(
                self._wake_event.wait(),
                timeout=max(1, self.check_interval),
            )
        except asyncio.TimeoutError:
            pass

    async def analyze_paper(self, paper_id: str) -> bool:
        """分析单篇论文，返回是否成功"""
        if not self.llm.is_configured():
            logger.warning("LLM 未配置，跳过论文分析: %s", paper_id)
            return False

        max_retries = 3
        self.current_paper_id = paper_id

        try:
            for attempt in range(max_retries):
                try:
                    paper_info = await asyncio.to_thread(get_paper, paper_id)
                    if not paper_info:
                        logger.error(f"论文 {paper_id} 不存在")
                        return False

                    logger.info(f"[{paper_id}] 读取 PDF...")
                    paper_content = None
                    content_error = None
                    if paper_info.get("pdf"):
                        try:
                            paper_content = await asyncio.to_thread(
                                get_or_cache_paper_content,
                                paper_id,
                                paper_info["pdf"],
                            )
                            paper_content = truncate_content_for_llm(paper_content)
                        except ReaderError as e:
                            content_error = str(e)
                            logger.warning(f"[{paper_id}] PDF 读取失败，改用论文元数据分析: {e}")
                    else:
                        content_error = "论文没有可用 PDF 链接"
                        logger.warning(f"[{paper_id}] 未找到 PDF 链接，改用论文元数据分析")

                    logger.info(f"[{paper_id}] 生成分析...")
                    user_prompt = build_analysis_prompt(paper_info, paper_content, content_error)
                    response = await self.llm.get_response(user_prompt)
                    response = normalize_llm_markdown(response, analysis_mode=True)

                    await asyncio.to_thread(update_llm_response, paper_id, response)
                    self.last_analyzed_paper_id = paper_id
                    logger.info(f"[{paper_id}] 分析完成: {paper_info.get('title', '')[:50]}")
                    return True

                except Exception as e:
                    logger.warning(f"[{paper_id}] 分析失败 (尝试 {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(2)

            logger.error(f"[{paper_id}] 分析失败，已重试 {max_retries} 次")
            return False
        finally:
            self.current_paper_id = None

    async def run(self):
        """主循环：每小时检查一次"""
        self.running = True
        logger.info(f"后台分析任务启动，检查间隔: {self.check_interval}秒")

        while self.running:
            try:
                self.last_run_started_at = datetime.now(timezone.utc)
                self.last_run_finished_at = None
                self.last_run_success_count = 0
                self.last_run_failed_count = 0
                self.last_run_error = None

                if not self.llm.is_configured():
                    logger.warning("LLM 未配置，跳过本轮后台分析")
                    self.last_run_error = "LLM is not configured"
                    self.last_run_finished_at = datetime.now(timezone.utc)
                    await self._sleep_until_next_check()
                    continue

                papers = await asyncio.to_thread(get_unanalyzed_papers, limit=10)

                if papers:
                    logger.info(f"发现 {len(papers)} 篇未分析论文，开始处理...")

                    for paper in papers:
                        if not self.running:
                            break

                        ok = await self.analyze_paper(paper["id"])
                        if ok:
                            self.last_run_success_count += 1
                        else:
                            self.last_run_failed_count += 1
                        await asyncio.sleep(1)

                    logger.info("本轮处理完成")
                else:
                    logger.info("没有未分析的论文")

            except Exception as e:
                self.last_run_error = str(e)[:500]
                logger.error(f"后台任务异常: {e}")
            finally:
                self.last_run_finished_at = datetime.now(timezone.utc)

            await self._sleep_until_next_check()

    def stop(self):
        """停止后台任务"""
        self.running = False
        self._wake_event.set()
        logger.info("后台分析任务停止")
