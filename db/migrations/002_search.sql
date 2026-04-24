CREATE INDEX IF NOT EXISTS idx_papers_title_fts
ON papers USING GIN (to_tsvector('english', COALESCE(title, '')));

CREATE INDEX IF NOT EXISTS idx_papers_abstract_fts
ON papers USING GIN (to_tsvector('english', COALESCE(abstract, '')));

CREATE INDEX IF NOT EXISTS idx_keywords_keyword_fts
ON keywords USING GIN (to_tsvector('english', COALESCE(keyword, '')));

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
DECLARE
  normalized_search_term TEXT;
  query_text tsquery;
BEGIN
  normalized_search_term := NULLIF(BTRIM(search_term), '');

  IF normalized_search_term IS NULL THEN
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
    ORDER BY
      CASE
        WHEN p.venue ILIKE '%oral%' THEN 1
        WHEN p.venue ILIKE '%spotlight%' THEN 2
        WHEN p.venue ILIKE '%poster%' THEN 3
        ELSE 4
      END ASC,
      COALESCE(LOWER(p.title), '') ASC,
      p.id ASC
    LIMIT page_limit OFFSET page_offset;

    RETURN;
  END IF;

  query_text := websearch_to_tsquery('english', normalized_search_term);

  RETURN QUERY
  WITH matched_papers AS (
    SELECT
      p.id,
      p.title,
      p.abstract,
      p.venue,
      p.primary_area,
      p.llm_response,
      p.created_at,
      (
        CASE
          WHEN search_title THEN
            ts_rank(
              setweight(to_tsvector('english', COALESCE(p.title, '')), 'A'),
              query_text
            )
          ELSE 0
        END
        +
        CASE
          WHEN search_abstract THEN
            ts_rank(
              setweight(to_tsvector('english', COALESCE(p.abstract, '')), 'B'),
              query_text
            )
          ELSE 0
        END
        +
        CASE
          WHEN search_keywords THEN
            COALESCE((
              SELECT MAX(
                ts_rank(
                  setweight(to_tsvector('english', COALESCE(k.keyword, '')), 'C'),
                  query_text
                )
              )
              FROM keywords k
              WHERE k.paper_id = p.id
                AND to_tsvector('english', COALESCE(k.keyword, '')) @@ query_text
            ), 0)
          ELSE 0
        END
      ) AS rank_score
    FROM papers p
    WHERE
      (venue_prefix IS NULL OR venue_prefix = '' OR p.venue ILIKE venue_prefix || '%')
      AND
      (
        (search_title AND to_tsvector('english', COALESCE(p.title, '')) @@ query_text)
        OR
        (search_abstract AND to_tsvector('english', COALESCE(p.abstract, '')) @@ query_text)
        OR
        (
          search_keywords AND EXISTS (
            SELECT 1
            FROM keywords k
            WHERE k.paper_id = p.id
              AND to_tsvector('english', COALESCE(k.keyword, '')) @@ query_text
          )
        )
      )
  )
  SELECT
    mp.id,
    mp.title,
    mp.abstract,
    mp.venue,
    mp.primary_area,
    mp.llm_response,
    mp.created_at
  FROM matched_papers mp
  ORDER BY
    mp.rank_score DESC,
    CASE
      WHEN mp.venue ILIKE '%oral%' THEN 1
      WHEN mp.venue ILIKE '%spotlight%' THEN 2
      WHEN mp.venue ILIKE '%poster%' THEN 3
      ELSE 4
    END ASC,
    COALESCE(LOWER(mp.title), '') ASC,
    mp.id ASC
  LIMIT page_limit OFFSET page_offset;
END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS count_papers_optimized(TEXT, TEXT, BOOLEAN, BOOLEAN, BOOLEAN);
CREATE OR REPLACE FUNCTION count_papers_optimized(
  search_term TEXT,
  venue_prefix TEXT,
  search_title BOOLEAN,
  search_abstract BOOLEAN,
  search_keywords BOOLEAN
)
RETURNS INTEGER AS $$
DECLARE
  normalized_search_term TEXT;
  query_text tsquery;
  total_count INTEGER;
BEGIN
  normalized_search_term := NULLIF(BTRIM(search_term), '');

  IF normalized_search_term IS NULL THEN
    SELECT COUNT(*)::INTEGER INTO total_count
    FROM papers p
    WHERE (venue_prefix IS NULL OR venue_prefix = '' OR p.venue ILIKE venue_prefix || '%');

    RETURN total_count;
  END IF;

  query_text := websearch_to_tsquery('english', normalized_search_term);

  SELECT COUNT(*)::INTEGER INTO total_count
  FROM papers p
  WHERE
    (venue_prefix IS NULL OR venue_prefix = '' OR p.venue ILIKE venue_prefix || '%')
    AND
    (
      (search_title AND to_tsvector('english', COALESCE(p.title, '')) @@ query_text)
      OR
      (search_abstract AND to_tsvector('english', COALESCE(p.abstract, '')) @@ query_text)
      OR
      (
        search_keywords AND EXISTS (
          SELECT 1
          FROM keywords k
          WHERE k.paper_id = p.id
            AND to_tsvector('english', COALESCE(k.keyword, '')) @@ query_text
        )
      )
    );

  RETURN total_count;
END;
$$ LANGUAGE plpgsql;
