CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL,
  email_normalized TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_login_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

CREATE TABLE IF NOT EXISTS user_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ,
  user_agent TEXT,
  ip_address TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id
ON user_sessions(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_sessions_active
ON user_sessions(token_hash, expires_at)
WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS paper_marks (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  viewed BOOLEAN NOT NULL DEFAULT FALSE,
  liked BOOLEAN NOT NULL DEFAULT FALSE,
  viewed_at TIMESTAMPTZ,
  liked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, paper_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_marks_user_updated
ON paper_marks(user_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_paper_marks_user_viewed_at
ON paper_marks(user_id, viewed_at DESC)
WHERE viewed;

CREATE INDEX IF NOT EXISTS idx_paper_marks_user_liked_at
ON paper_marks(user_id, liked_at DESC)
WHERE liked;

CREATE INDEX IF NOT EXISTS idx_paper_marks_paper
ON paper_marks(paper_id);

CREATE TABLE IF NOT EXISTS presence_heartbeats (
  client_id TEXT PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  user_agent TEXT,
  ip_address TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_presence_heartbeats_last_seen
ON presence_heartbeats(last_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_presence_heartbeats_user_id
ON presence_heartbeats(user_id);

CREATE TABLE IF NOT EXISTS presence_snapshots (
  bucket_at TIMESTAMPTZ PRIMARY KEY,
  total_count INTEGER NOT NULL,
  authenticated_count INTEGER NOT NULL,
  guest_count INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_presence_snapshots_created
ON presence_snapshots(bucket_at DESC);

ALTER TABLE chat_sessions
  ADD COLUMN IF NOT EXISTS account_user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_chat_sessions_account_paper
ON chat_sessions(account_user_id, paper_id, created_at DESC);
