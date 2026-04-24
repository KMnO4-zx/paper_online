CREATE TABLE IF NOT EXISTS user_feishu_settings (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  webhook_url TEXT NOT NULL,
  daily_push_count INTEGER NOT NULL DEFAULT 3 CHECK (daily_push_count BETWEEN 1 AND 5),
  enabled BOOLEAN NOT NULL DEFAULT FALSE,
  last_tested_at TIMESTAMPTZ,
  last_test_status TEXT,
  last_test_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_feishu_settings_enabled
ON user_feishu_settings(enabled)
WHERE enabled;

CREATE TABLE IF NOT EXISTS feishu_push_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  daily_date DATE NOT NULL,
  paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'skipped')),
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, daily_date, paper_id)
);

CREATE INDEX IF NOT EXISTS idx_feishu_push_logs_user_date
ON feishu_push_logs(user_id, daily_date DESC);

CREATE INDEX IF NOT EXISTS idx_feishu_push_logs_date_status
ON feishu_push_logs(daily_date DESC, status);
