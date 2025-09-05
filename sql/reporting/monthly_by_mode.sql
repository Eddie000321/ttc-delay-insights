-- Monthly event counts by mode
SELECT
  date_trunc('month', date)::date AS month,
  source,
  COUNT(*) AS n
FROM ttc_delays
GROUP BY 1, 2
ORDER BY 1, 2;

