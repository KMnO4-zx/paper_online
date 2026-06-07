CREATE INDEX IF NOT EXISTS idx_hf_daily_papers_paper_latest
ON hf_daily_papers(paper_id ASC, daily_date DESC, upvotes DESC, rank ASC, id DESC);
