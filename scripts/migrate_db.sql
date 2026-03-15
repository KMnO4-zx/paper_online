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

-- RPC search function for paginated paper search
DROP FUNCTION IF EXISTS search_papers_optimized(TEXT, TEXT, BOOLEAN, BOOLEAN, BOOLEAN, INT, INT);
CREATE OR REPLACE FUNCTION search_papers_optimized(
  search_term TEXT,
  venue_prefix TEXT,
  search_title BOOLEAN,
  search_abstract BOOLEAN,
  search_keywords BOOLEAN,
  page_limit INT,
  page_offset INT
)
RETURNS TABLE(
  id TEXT,
  title TEXT,
  abstract TEXT,
  venue TEXT,
  primary_area TEXT,
  llm_response TEXT,
  created_at TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    p.title,
    p.abstract,
    p.venue,
    p.primary_area,
    p.llm_response,
    p.created_at
  FROM papers p
  WHERE
    (venue_prefix IS NULL OR venue_prefix = '' OR p.venue ILIKE venue_prefix || '%')
    AND
    (
      search_term IS NULL OR search_term = '' OR
      (
        (search_title AND p.title ILIKE '%' || search_term || '%') OR
        (search_abstract AND p.abstract ILIKE '%' || search_term || '%') OR
        (
          search_keywords AND EXISTS (
            SELECT 1
            FROM keywords k
            WHERE k.paper_id = p.id
              AND k.keyword ILIKE '%' || search_term || '%'
          )
        )
      )
    )
  ORDER BY
    CASE
      WHEN p.venue ILIKE '%oral%' THEN 1
      WHEN p.venue ILIKE '%spotlight%' THEN 2
      WHEN p.venue ILIKE '%poster%' THEN 3
      ELSE 4
    END ASC,
    p.created_at DESC
  LIMIT page_limit OFFSET page_offset;
END;
$$ LANGUAGE plpgsql;

-- RPC count function for matching papers
CREATE OR REPLACE FUNCTION count_papers_optimized(
  search_term TEXT,
  venue_prefix TEXT,
  search_title BOOLEAN,
  search_abstract BOOLEAN,
  search_keywords BOOLEAN
)
RETURNS INTEGER AS $$
DECLARE
  total_count INTEGER;
BEGIN
  SELECT COUNT(*)::INTEGER INTO total_count
  FROM papers p
  WHERE
    (venue_prefix IS NULL OR venue_prefix = '' OR p.venue ILIKE venue_prefix || '%')
    AND
    (
      search_term IS NULL OR search_term = '' OR
      (
        (search_title AND p.title ILIKE '%' || search_term || '%') OR
        (search_abstract AND p.abstract ILIKE '%' || search_term || '%') OR
        (
          search_keywords AND EXISTS (
            SELECT 1
            FROM keywords k
            WHERE k.paper_id = p.id
              AND k.keyword ILIKE '%' || search_term || '%'
          )
        )
      )
    );

  RETURN total_count;
END;
$$ LANGUAGE plpgsql;

-- Note: The following operations should be done carefully if you have existing data
-- Remove pdf column (can be constructed from id)
-- ALTER TABLE papers DROP COLUMN IF EXISTS pdf;

-- Remove keywords array column (moved to separate table)
-- ALTER TABLE papers DROP COLUMN IF EXISTS keywords;
