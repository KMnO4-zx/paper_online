import logging
import re
from datetime import date
from typing import Any

import requests

logger = logging.getLogger(__name__)

FEISHU_WEBHOOK_PATTERN = re.compile(
    r"^https://open\.feishu\.cn/open-apis/bot/v2/hook/[A-Za-z0-9-]+$"
)
FEISHU_TIMEOUT_SECONDS = 10
MAX_ANALYSIS_CHARS = 6000


class FeishuWebhookError(Exception):
    """Raised when a Feishu webhook request is rejected or cannot be sent."""


def validate_feishu_webhook_url(webhook_url: str) -> str:
    normalized = (webhook_url or "").strip()
    if not FEISHU_WEBHOOK_PATTERN.match(normalized):
        raise ValueError("飞书 webhook URL 格式不正确")
    return normalized


def mask_feishu_webhook_url(webhook_url: str | None) -> str | None:
    if not webhook_url:
        return None
    token = webhook_url.rstrip("/").split("/")[-1]
    if len(token) <= 12:
        masked_token = f"{token[:2]}...{token[-2:]}"
    else:
        masked_token = f"{token[:8]}...{token[-4:]}"
    return webhook_url.rsplit("/", 1)[0] + "/" + masked_token


def _truncate_text(value: Any, max_chars: int) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n...（内容过长，已截断）"


def build_feishu_paper_card(paper: dict, daily_date: date | str) -> dict:
    title = str(paper.get("title") or paper.get("id") or "Paper Insight Daily Paper").strip()
    analysis = _truncate_text(paper.get("llm_response"), MAX_ANALYSIS_CHARS)
    if not analysis:
        raise FeishuWebhookError("论文缺少 AI 分析")

    hf_daily = paper.get("hf_daily") or {}
    meta_parts = []
    if hf_daily.get("rank"):
        meta_parts.append(f"Rank: {hf_daily['rank']}")
    if hf_daily.get("upvotes") is not None:
        meta_parts.append(f"Upvotes: {hf_daily['upvotes']}")
    if paper.get("pdf"):
        meta_parts.append(f"[PDF]({paper['pdf']})")
    if hf_daily.get("project_page"):
        meta_parts.append(f"[Project]({hf_daily['project_page']})")
    if hf_daily.get("github_repo"):
        meta_parts.append(f"[GitHub]({hf_daily['github_repo']})")

    meta_line = " · ".join(meta_parts) if meta_parts else "Hugging Face Daily Paper"
    body = (
        f"📘 **Hugging Face Daily Papers · {daily_date}**\n\n"
        f"{meta_line}\n\n"
        "🤖 **AI 分析**\n\n"
        f"{analysis}"
    )

    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {
                    "tag": "plain_text",
                    "content": title,
                },
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": body,
                    },
                }
            ],
        },
    }


def build_feishu_test_card() -> dict:
    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {
                    "tag": "plain_text",
                    "content": "Paper Insight 飞书推送测试",
                },
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "如果你看到这张卡片，说明每日论文推送 webhook 已配置成功。",
                    },
                }
            ],
        },
    }


def send_feishu_payload(webhook_url: str, payload: dict) -> dict:
    try:
        normalized_url = validate_feishu_webhook_url(webhook_url)
    except ValueError as exc:
        raise FeishuWebhookError(str(exc)) from exc

    try:
        response = requests.post(
            normalized_url,
            json=payload,
            timeout=FEISHU_TIMEOUT_SECONDS,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        logger.warning("飞书 webhook 请求失败: %s", exc)
        raise FeishuWebhookError("飞书 webhook 请求失败") from exc

    code = result.get("code", result.get("StatusCode"))
    if code != 0:
        message = result.get("msg") or result.get("StatusMessage") or "飞书 webhook 返回失败"
        raise FeishuWebhookError(str(message))
    return result
