-- Daily counts by source
CREATE OR REPLACE VIEW vw_daily_counts AS
SELECT
  date::date AS date,
  source,
  COUNT(*) AS n
FROM ttc_delays
GROUP BY 1, 2;

