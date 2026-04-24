CREATE TABLE IF NOT EXISTS papers (
  id TEXT PRIMARY KEY,
  title TEXT,
  abstract TEXT,
  keywords JSONB,
  pdf TEXT,
  venue TEXT,
  primary_area TEXT,
  llm_response TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE papers
  ADD COLUMN IF NOT EXISTS keywords JSONB,
  ADD COLUMN IF NOT EXISTS pdf TEXT,
  ADD COLUMN IF NOT EXISTS venue TEXT,
  ADD COLUMN IF NOT EXISTS primary_area TEXT,
  ADD COLUMN IF NOT EXISTS llm_response TEXT,
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE papers
  ALTER COLUMN title DROP NOT NULL;

CREATE TABLE IF NOT EXISTS authors (
  id SERIAL PRIMARY KEY,
  paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  author_name TEXT NOT NULL,
  author_order INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_authors_paper_id ON authors(paper_id);

CREATE TABLE IF NOT EXISTS keywords (
  id SERIAL PRIMARY KEY,
  paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  keyword TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_keywords_paper_id ON keywords(paper_id);

CREATE TABLE IF NOT EXISTS chat_sessions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  title TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_paper
ON chat_sessions(user_id, paper_id, created_at DESC);

CREATE TABLE IF NOT EXISTS chat_messages (
  id BIGSERIAL PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session
ON chat_messages(session_id, created_at);
