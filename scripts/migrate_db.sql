-- Database Migration for Paper Online
-- Execute this in Supabase SQL Editor

-- Create authors table
CREATE TABLE IF NOT EXISTS authors (
  id SERIAL PRIMARY KEY,
  paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  author_name TEXT NOT NULL,
  author_order INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_authors_paper_id ON authors(paper_id);

-- Create keywords table
CREATE TABLE IF NOT EXISTS keywords (
  id SERIAL PRIMARY KEY,
  paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  keyword TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_keywords_paper_id ON keywords(paper_id);

-- Add new columns to papers table
ALTER TABLE papers ADD COLUMN IF NOT EXISTS venue TEXT;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS primary_area TEXT;

-- Note: The following operations should be done carefully if you have existing data
-- Remove pdf column (can be constructed from id)
-- ALTER TABLE papers DROP COLUMN IF EXISTS pdf;

-- Remove keywords array column (moved to separate table)
-- ALTER TABLE papers DROP COLUMN IF EXISTS keywords;
