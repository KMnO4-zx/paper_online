import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from feishu import (  # noqa: E402
    FeishuWebhookError,
    build_feishu_paper_card,
    mask_feishu_webhook_url,
    validate_feishu_webhook_url,
)


def test_validate_feishu_webhook_url_accepts_v2_hook():
    url = "https://open.feishu.cn/open-apis/bot/v2/hook/11111111-2222-3333-4444-555555555555"

    assert validate_feishu_webhook_url(f" {url} ") == url


def test_validate_feishu_webhook_url_rejects_non_feishu_url():
    with pytest.raises(ValueError):
        validate_feishu_webhook_url("https://example.com/open-apis/bot/v2/hook/not-feishu")


def test_mask_feishu_webhook_url_hides_secret_token():
    masked = mask_feishu_webhook_url(
        "https://open.feishu.cn/open-apis/bot/v2/hook/11111111-2222-3333-4444-555555555555"
    )

    assert masked == "https://open.feishu.cn/open-apis/bot/v2/hook/11111111...5555"


def test_build_feishu_paper_card_uses_title_and_ai_analysis():
    payload = build_feishu_paper_card(
        {
            "id": "hf:2604.00001",
            "title": "A Good Paper",
            "pdf": "https://arxiv.org/pdf/2604.00001",
            "llm_response": "这是 AI 分析。",
            "hf_daily": {"rank": 1, "upvotes": 123},
        },
        date(2026, 4, 24),
    )

    assert payload["msg_type"] == "interactive"
    assert payload["card"]["header"]["title"]["content"] == "A Good Paper"
    content = payload["card"]["elements"][0]["text"]["content"]
    assert "Upvotes: 123" in content
    assert "这是 AI 分析。" in content


def test_build_feishu_paper_card_requires_ai_analysis():
    with pytest.raises(FeishuWebhookError):
        build_feishu_paper_card({"id": "hf:2604.00001", "title": "A Good Paper"}, "2026-04-24")
