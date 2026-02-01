import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "papers.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            title TEXT,
            abstract TEXT,
            keywords TEXT,
            pdf TEXT,
            llm_response TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_paper(paper_id: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "abstract": row[2],
        "keywords": json.loads(row[3]) if row[3] else [],
        "pdf": row[4],
        "llm_response": row[5]
    }


def save_paper(paper_info: dict, llm_response: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO papers (id, title, abstract, keywords, pdf, llm_response)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        paper_info["id"],
        paper_info.get("title"),
        paper_info.get("abstract"),
        json.dumps(paper_info.get("keywords", [])),
        paper_info.get("pdf"),
        llm_response
    ))
    conn.commit()
    conn.close()


def update_llm_response(paper_id: str, response: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE papers SET llm_response = ? WHERE id = ?",
        (response, paper_id)
    )
    conn.commit()
    conn.close()


init_db()
