CREATE TABLE IF NOT EXISTS hf_daily_papers (
  id BIGSERIAL PRIMARY KEY,
  daily_date DATE NOT NULL,
  paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  rank INTEGER NOT NULL CHECK (rank > 0),
  upvotes INTEGER NOT NULL DEFAULT 0,
  thumbnail TEXT,
  discussion_id TEXT,
  project_page TEXT,
  github_repo TEXT,
  github_stars INTEGER,
  num_comments INTEGER,
  raw JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (daily_date, paper_id)
);

CREATE INDEX IF NOT EXISTS idx_hf_daily_papers_date_rank
ON hf_daily_papers(daily_date DESC, rank ASC);

CREATE INDEX IF NOT EXISTS idx_hf_daily_papers_paper
ON hf_daily_papers(paper_id);
