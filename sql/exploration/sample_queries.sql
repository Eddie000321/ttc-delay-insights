-- A couple of quick checks for exploration

-- Recent rows (sanity check)
SELECT *
FROM ttc_delays
ORDER BY date DESC, time DESC NULLS LAST
LIMIT 100;

-- Null distribution for critical columns
SELECT
  SUM(CASE WHEN date IS NULL THEN 1 ELSE 0 END) AS null_date,
  SUM(CASE WHEN station IS NULL THEN 1 ELSE 0 END) AS null_station,
  SUM(CASE WHEN source IS NULL THEN 1 ELSE 0 END) AS null_source
FROM ttc_delays;

