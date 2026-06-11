from __future__ import annotations

from typing import Any


def build_analysis_prompt(paper_info: dict[str, Any], paper_content: str | None, content_error: str | None = None) -> str:
    if paper_content:
        return f"以下是论文内容：\n{paper_content}"

    metadata_context = build_paper_metadata_context(paper_info, content_error=content_error)
    return f"以下是论文元数据。未能获取论文全文时，请只基于这些信息做初筛分析；无法判断的内容必须明确写“未知”，不要编造。\n\n{metadata_context}"


def build_chat_context_parts(
    paper_info: dict[str, Any],
    paper_content: str | None,
    content_error: str | None = None,
) -> list[str]:
    if paper_content:
        return [f"论文全文：\n{paper_content}"]
    return [build_paper_metadata_context(paper_info, content_error=content_error)]


def build_paper_metadata_context(paper_info: dict[str, Any], content_error: str | None = None) -> str:
    lines = [
        "论文元数据：",
        f"标题：{_value(paper_info.get('title'))}",
        f"会议：{_value(paper_info.get('venue'))}",
        f"领域/分组：{_value(paper_info.get('primary_area'))}",
        f"作者：{_join_values(paper_info.get('authors'))}",
        f"关键词：{_join_values(paper_info.get('keywords'))}",
        f"PDF：{_value(paper_info.get('pdf'))}",
        f"摘要：{_value(paper_info.get('abstract'))}",
    ]
    if content_error:
        lines.append(f"全文读取状态：未能获取论文全文；原因：{content_error}")
    return "\n".join(lines)


def _value(value: Any) -> str:
    if value is None:
        return "未知"
    text = str(value).strip()
    return text or "未知"


def _join_values(values: Any) -> str:
    if not values:
        return "未知"
    if isinstance(values, str):
        return values
    try:
        joined = "；".join(str(value).strip() for value in values if str(value).strip())
    except TypeError:
        return _value(values)
    return joined or "未知"
