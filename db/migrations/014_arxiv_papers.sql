CREATE TABLE IF NOT EXISTS arxiv_papers (
  id BIGSERIAL PRIMARY KEY,
  paper_id TEXT NOT NULL UNIQUE REFERENCES papers(id) ON DELETE CASCADE,
  arxiv_id TEXT NOT NULL UNIQUE,
  arxiv_url TEXT NOT NULL,
  pdf_url TEXT NOT NULL,
  published_at TIMESTAMPTZ,
  arxiv_updated_at TIMESTAMPTZ,
  added_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_arxiv_papers_added_at
ON arxiv_papers(added_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_arxiv_papers_published_at
ON arxiv_papers(published_at DESC);

CREATE INDEX IF NOT EXISTS idx_arxiv_papers_added_by_user
ON arxiv_papers(added_by_user_id, added_at DESC);
