-- Top stations by count within a date range and mode
-- Parameters (psql):
--   \set source 'subway'
--   \set from '2024-01-01'
--   \set to   '2024-12-31'

SELECT station, COUNT(*) AS n
FROM ttc_delays
WHERE source = :source
  AND date >= to_date(:from, 'YYYY-MM-DD')
  AND date <  to_date(:to,   'YYYY-MM-DD') + INTERVAL '1 day'
GROUP BY station
ORDER BY n DESC
LIMIT 20;

