CREATE TABLE IF NOT EXISTS invitation_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code_hash TEXT NOT NULL UNIQUE,
  code_text TEXT,
  code_prefix TEXT NOT NULL,
  max_uses INTEGER NOT NULL CHECK (max_uses > 0),
  used_count INTEGER NOT NULL DEFAULT 0 CHECK (used_count >= 0),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,
  CHECK (used_count <= max_uses)
);

ALTER TABLE invitation_codes
  ADD COLUMN IF NOT EXISTS code_text TEXT;

CREATE INDEX IF NOT EXISTS idx_invitation_codes_created
ON invitation_codes(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_invitation_codes_active
ON invitation_codes(is_active, used_count, max_uses);
