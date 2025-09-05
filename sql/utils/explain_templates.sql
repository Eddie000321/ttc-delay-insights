-- Template for performance analysis with parameters
-- Requires: \set from, \set to (see sql/snippets/date_params.psql)

EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT *
FROM ttc_delays
WHERE date >= to_date(:from, 'YYYY-MM-DD')
  AND date <  to_date(:to,   'YYYY-MM-DD') + INTERVAL '1 day'
ORDER BY date DESC
LIMIT 100;

