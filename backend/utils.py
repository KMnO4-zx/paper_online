import requests
import time
import logging
import tiktoken

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TIMEOUT = 30
MAX_RETRIES = 3
LLM_CONTENT_TOKEN_LIMIT = 180000
_TOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")

HEADERS = {
    "Accept": "application/json,text/*;q=0.99",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Referer": "https://openreview.net/",
    "Origin": "https://openreview.net"
}


class ReaderError(Exception):
    """Jina Reader 请求失败"""
    pass


class OpenReviewError(Exception):
    """OpenReview API 请求失败"""
    pass


def truncate_content_for_llm(text: str, max_tokens: int = LLM_CONTENT_TOKEN_LIMIT) -> str:
    token_ids = _TOKEN_ENCODING.encode(text)
    token_count = len(token_ids)

    if token_count <= max_tokens:
        logger.info(f"LLM content within token limit: {token_count} <= {max_tokens}")
        return text

    truncated_text = _TOKEN_ENCODING.decode(token_ids[:max_tokens])
    logger.warning(
        "LLM content truncated by tokens: original=%s, kept=%s",
        token_count,
        max_tokens,
    )
    return truncated_text


def reader(url: str) -> str:
    target_url = "https://r.jina.ai/" + url

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(target_url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.Timeout:
            logger.warning(f"Jina Reader 超时 (尝试 {attempt + 1}/{MAX_RETRIES})")
        except requests.RequestException as e:
            logger.warning(f"Jina Reader 请求失败: {e} (尝试 {attempt + 1}/{MAX_RETRIES})")

        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)

    raise ReaderError(f"Jina Reader 请求失败，已重试 {MAX_RETRIES} 次: {url}")

def get_openreview_info(paper_id: str) -> dict | None:
    url = f"https://api2.openreview.net/notes?id={paper_id}"

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if not data.get("notes"):
                return None

            note = data["notes"][0]
            content = note.get("content", {})

            return {
                "id": note.get("id"),
                "title": content.get("title", {}).get("value"),
                "abstract": content.get("abstract", {}).get("value"),
                "authors": content.get("authors", {}).get("value", []),
                "keywords": content.get("keywords", {}).get("value", []),
                "primary_area": content.get("primary_area", {}).get("value"),
                "venue": content.get("venue", {}).get("value"),
                "pdf": f"https://openreview.net/attachment?id={note['id']}&name=pdf",
            }
        except requests.Timeout:
            logger.warning(f"OpenReview API 超时 (尝试 {attempt + 1}/{MAX_RETRIES})")
        except requests.RequestException as e:
            logger.warning(f"OpenReview API 请求失败: {e} (尝试 {attempt + 1}/{MAX_RETRIES})")

        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)

    raise OpenReviewError(f"OpenReview API 请求失败，已重试 {MAX_RETRIES} 次: {paper_id}")



if __name__ == "__main__":
    sample_url = "https://openreview.net/attachment?id=uq6UWRgzMr&name=pdf"
    # content = reader(sample_url)
    # print(content)

    # paper_id = "uq6UWRgzMr"
    # info = get_openreview_info(paper_id)
    # print(info)
