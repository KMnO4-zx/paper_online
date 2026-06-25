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
      COALESCE(p.sort_order, 2147483647) ASC,
      COALESCE(LOWER(p.title), '') ASC,
      p.id ASC
    LIMIT page_limit OFFSET page_offset;

    RETURN;
  END IF;

  query_text := websearch_to_tsquery('english', normalized_search_term);

  RETURN QUERY
  WITH title_matches AS (
    SELECT
      p.id,
      ts_rank(to_tsvector('english', COALESCE(p.title, '')), query_text)::DOUBLE PRECISION * 1.0 AS rank_score
    FROM papers p
    WHERE
      search_title
      AND (venue_prefix IS NULL OR venue_prefix = '' OR p.venue ILIKE venue_prefix || '%')
      AND to_tsvector('english', COALESCE(p.title, '')) @@ query_text
  ),
  keyword_matches AS (
    SELECT
      k.paper_id AS id,
      MAX(ts_rank(to_tsvector('english', COALESCE(k.keyword, '')), query_text)::DOUBLE PRECISION * 0.55) AS rank_score
    FROM keywords k
    JOIN papers p ON p.id = k.paper_id
    WHERE
      search_keywords
      AND (venue_prefix IS NULL OR venue_prefix = '' OR p.venue ILIKE venue_prefix || '%')
      AND to_tsvector('english', COALESCE(k.keyword, '')) @@ query_text
    GROUP BY k.paper_id
  ),
  abstract_matches AS (
    SELECT
      p.id,
      ts_rank(to_tsvector('english', COALESCE(p.abstract, '')), query_text)::DOUBLE PRECISION * 0.35 AS rank_score
    FROM papers p
    WHERE
      search_abstract
      AND (venue_prefix IS NULL OR venue_prefix = '' OR p.venue ILIKE venue_prefix || '%')
      AND to_tsvector('english', COALESCE(p.abstract, '')) @@ query_text
  ),
  ranked_papers AS (
    SELECT
      candidates.id,
      SUM(candidates.rank_score) AS rank_score
    FROM (
      SELECT tm.id, tm.rank_score FROM title_matches tm
      UNION ALL
      SELECT km.id, km.rank_score FROM keyword_matches km
      UNION ALL
      SELECT am.id, am.rank_score FROM abstract_matches am
    ) candidates
    GROUP BY candidates.id
  ),
  matched_papers AS (
    SELECT
      p.id,
      p.title,
      p.abstract,
      p.venue,
      p.primary_area,
      p.llm_response,
      p.created_at,
      p.sort_order,
      rp.rank_score
    FROM ranked_papers rp
    JOIN papers p ON p.id = rp.id
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
    -- Treat extremely close scores as a tie so presentation type can break near-ties.
    ROUND(mp.rank_score::NUMERIC, 4) DESC,
    CASE
      WHEN mp.venue ILIKE '%oral%' THEN 1
      WHEN mp.venue ILIKE '%spotlight%' THEN 2
      WHEN mp.venue ILIKE '%poster%' THEN 3
      ELSE 4
    END ASC,
    mp.rank_score DESC,
    COALESCE(mp.sort_order, 2147483647) ASC,
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

  WITH candidate_ids AS (
    SELECT p.id
    FROM papers p
    WHERE
      search_title
      AND (venue_prefix IS NULL OR venue_prefix = '' OR p.venue ILIKE venue_prefix || '%')
      AND to_tsvector('english', COALESCE(p.title, '')) @@ query_text

    UNION

    SELECT p.id
    FROM papers p
    WHERE
      search_abstract
      AND (venue_prefix IS NULL OR venue_prefix = '' OR p.venue ILIKE venue_prefix || '%')
      AND to_tsvector('english', COALESCE(p.abstract, '')) @@ query_text

    UNION

    SELECT k.paper_id AS id
    FROM keywords k
    JOIN papers p ON p.id = k.paper_id
    WHERE
      search_keywords
      AND (venue_prefix IS NULL OR venue_prefix = '' OR p.venue ILIKE venue_prefix || '%')
      AND to_tsvector('english', COALESCE(k.keyword, '')) @@ query_text
  )
  SELECT COUNT(*)::INTEGER INTO total_count
  FROM candidate_ids;

  RETURN total_count;
END;
$$ LANGUAGE plpgsql;
