from __future__ import annotations

import json
import re
from typing import Any

from prompt import CODE_AVAILABILITY_PROMPT

CODE_AVAILABILITY_STATUSES = {"open_source", "unavailable", "not_found", "unknown"}


def normalize_code_availability_status(value: object) -> str:
    status = str(value or "").strip().lower()
    return status if status in CODE_AVAILABILITY_STATUSES else "unknown"


def normalize_code_url(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "null":
        return None
    return text


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("code availability response is not a JSON object")
    return parsed


def normalize_code_availability_result(raw_result: dict[str, Any]) -> dict[str, Any]:
    status = normalize_code_availability_status(raw_result.get("status"))
    code_url = normalize_code_url(raw_result.get("code_url"))
    if status != "open_source":
        code_url = None

    evidence = str(raw_result.get("evidence") or "").strip()
    reason = str(raw_result.get("reason") or "").strip()
    try:
        confidence = float(raw_result.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0.0

    return {
        "status": status,
        "code_url": code_url,
        "evidence": evidence[:2000],
        "meta": {
            "confidence": max(0.0, min(confidence, 1.0)),
            "reason": reason[:2000],
        },
    }


async def classify_code_availability_from_text(
    llm,
    paper_info: dict[str, Any],
    source_text: str | None,
    *,
    source: str = "llm_response",
) -> dict[str, Any]:
    text = (source_text or "").strip()
    if not text:
        return {
            "status": "unknown",
            "code_url": None,
            "evidence": "没有可用于判断代码开源状态的文本。",
            "meta": {"confidence": 0.0, "reason": "empty_source_text", "source": source},
        }

    user_prompt = "\n".join(
        [
            f"paper_id: {paper_info.get('id') or ''}",
            f"title: {paper_info.get('title') or ''}",
            f"venue: {paper_info.get('venue') or ''}",
            f"source: {source}",
            "",
            "待判断文本：",
            text,
        ]
    )

    raw_response = await llm.chat(
        [
            {"role": "system", "content": CODE_AVAILABILITY_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        _usage_context="code_availability",
    )

    try:
        parsed = _extract_json_object(raw_response or "")
        normalized = normalize_code_availability_result(parsed)
    except Exception as exc:
        return {
            "status": "unknown",
            "code_url": None,
            "evidence": f"代码开源状态判断结果无法解析：{exc}",
            "meta": {
                "confidence": 0.0,
                "reason": "parse_error",
                "source": source,
                "raw_response": (raw_response or "")[:2000],
            },
        }

    normalized["meta"] = {
        **normalized["meta"],
        "source": source,
    }
    return normalized
