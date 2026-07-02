import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from code_availability import classify_code_availability_from_text


class BlockedLLM:
    async def chat(self, messages, **kwargs):
        raise RuntimeError(
            "Error code: 451 - {'error': {'message': 'The content you provided or machine outputted is blocked.', "
            "'type': 'censorship_blocked'}}"
        )


@pytest.mark.asyncio
async def test_code_availability_content_block_is_recordable_unknown():
    result = await classify_code_availability_from_text(
        BlockedLLM(),
        {"id": "paper-1", "title": "Adversarial paper"},
        "analysis text",
    )

    assert result["status"] == "unknown"
    assert result["code_url"] is None
    assert result["meta"]["reason"] == "provider_content_blocked"
