import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from llm import _stream_params_with_usage, iter_llm_stream_chunks


def make_chunk(delta):
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


def test_iter_llm_stream_chunks_reads_step_reasoning_field():
    chunk = make_chunk(SimpleNamespace(reasoning="thinking", content="answer"))

    chunks = list(iter_llm_stream_chunks(chunk))

    assert [(chunk.kind, chunk.content) for chunk in chunks] == [
        ("reasoning", "thinking"),
        ("content", "answer"),
    ]


def test_iter_llm_stream_chunks_reads_deepseek_reasoning_content_field():
    chunk = make_chunk(SimpleNamespace(reasoning_content="thinking", content="answer"))

    chunks = list(iter_llm_stream_chunks(chunk))

    assert [(chunk.kind, chunk.content) for chunk in chunks] == [
        ("reasoning", "thinking"),
        ("content", "answer"),
    ]


def test_iter_llm_stream_chunks_reads_unknown_fields_from_model_extra():
    delta = SimpleNamespace(content=None, model_extra={"reasoning_content": "thinking"})

    chunks = list(iter_llm_stream_chunks(make_chunk(delta)))

    assert [(chunk.kind, chunk.content) for chunk in chunks] == [("reasoning", "thinking")]


def test_stream_params_request_usage_without_dropping_existing_options():
    params = _stream_params_with_usage({"stream_options": {"foo": "bar"}, "max_tokens": 10})

    assert params["stream_options"] == {"foo": "bar", "include_usage": True}
    assert params["max_tokens"] == 10
