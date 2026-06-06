CREATE INDEX IF NOT EXISTS idx_hf_daily_papers_date_upvotes
ON hf_daily_papers(daily_date DESC, upvotes DESC, rank ASC, paper_id ASC);
