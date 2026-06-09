CREATE TABLE IF NOT EXISTS llm_token_usage (
  id BIGSERIAL PRIMARY KEY,
  provider_id UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
  provider_key TEXT,
  provider_name TEXT,
  model_name TEXT NOT NULL,
  request_type TEXT NOT NULL DEFAULT 'unknown',
  input_tokens BIGINT NOT NULL DEFAULT 0,
  output_tokens BIGINT NOT NULL DEFAULT 0,
  cache_input_tokens BIGINT NOT NULL DEFAULT 0,
  cache_output_tokens BIGINT NOT NULL DEFAULT 0,
  total_tokens BIGINT NOT NULL DEFAULT 0,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE llm_token_usage
  ADD COLUMN IF NOT EXISTS provider_id UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS provider_key TEXT,
  ADD COLUMN IF NOT EXISTS provider_name TEXT,
  ADD COLUMN IF NOT EXISTS model_name TEXT,
  ADD COLUMN IF NOT EXISTS request_type TEXT NOT NULL DEFAULT 'unknown',
  ADD COLUMN IF NOT EXISTS input_tokens BIGINT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS output_tokens BIGINT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS cache_input_tokens BIGINT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS cache_output_tokens BIGINT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS total_tokens BIGINT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_llm_token_usage_created
ON llm_token_usage(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_llm_token_usage_model_created
ON llm_token_usage(model_name, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_llm_token_usage_provider_created
ON llm_token_usage(provider_id, created_at DESC);
