ALTER TABLE paper_marks
  ADD COLUMN IF NOT EXISTS favorited BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS favorited_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_paper_marks_user_favorited_at
ON paper_marks(user_id, favorited_at DESC)
WHERE favorited;
