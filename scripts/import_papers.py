#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(env_path)

from supabase import create_client

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials not found in environment variables")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def import_conference(conference_name: str):
    """Import papers from a conference directory."""
    data_dir = Path(__file__).parent.parent / "crawled_data" / conference_name

    if not data_dir.exists():
        print(f"Error: Directory {data_dir} does not exist")
        return

    jsonl_files = list(data_dir.glob("*.jsonl"))
    if not jsonl_files:
        print(f"No JSONL files found in {data_dir}")
        return

    total_papers = 0
    BATCH_SIZE = 100

    for jsonl_file in jsonl_files:
        print(f"\nProcessing {jsonl_file.name}...")

        papers_batch = []
        authors_batch = []
        keywords_batch = []

        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    paper = json.loads(line)
                    paper_id = paper["id"]
                    content = paper["content"]

                    papers_batch.append({
                        "id": paper_id,
                        "title": content["title"]["value"],
                        "abstract": content["abstract"]["value"],
                        "venue": content["venue"]["value"],
                        "primary_area": content["primary_area"]["value"]
                    })

                    for i, author in enumerate(content["authors"]["value"]):
                        authors_batch.append({
                            "paper_id": paper_id,
                            "author_name": author,
                            "author_order": i
                        })

                    for keyword in content["keywords"]["value"]:
                        keywords_batch.append({
                            "paper_id": paper_id,
                            "keyword": keyword
                        })

                    if len(papers_batch) >= BATCH_SIZE:
                        _insert_batch(papers_batch, authors_batch, keywords_batch)
                        total_papers += len(papers_batch)
                        print(f"  Imported {total_papers} papers...")
                        papers_batch = []
                        authors_batch = []
                        keywords_batch = []

                except Exception as e:
                    print(f"  Error on line {line_num}: {e}")
                    continue

        if papers_batch:
            _insert_batch(papers_batch, authors_batch, keywords_batch)
            total_papers += len(papers_batch)

    print(f"\n✓ Successfully imported {total_papers} papers from {conference_name}")


def _insert_batch(papers, authors, keywords):
    """Insert a batch of papers, authors, and keywords."""
    if papers:
        supabase.table("papers").upsert(papers).execute()
    if authors:
        paper_ids = list(set(a["paper_id"] for a in authors))
        for pid in paper_ids:
            supabase.table("authors").delete().eq("paper_id", pid).execute()
        supabase.table("authors").insert(authors).execute()
    if keywords:
        paper_ids = list(set(k["paper_id"] for k in keywords))
        for pid in paper_ids:
            supabase.table("keywords").delete().eq("paper_id", pid).execute()
        supabase.table("keywords").insert(keywords).execute()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import papers from JSONL files to Supabase")
    parser.add_argument("--conference", required=True, help="Conference name (e.g., neurips_2025, iclr_2026)")

    args = parser.parse_args()

    import_conference(args.conference)
