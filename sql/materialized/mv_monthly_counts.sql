-- Monthly counts by source (materialized)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_monthly_counts AS
SELECT
  date_trunc('month', date)::date AS month,
  source,
  COUNT(*) AS n
FROM ttc_delays
GROUP BY 1, 2
WITH NO DATA;

-- Indexes for fast filtering and to enable CONCURRENT refresh
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_monthly_counts_month_source
  ON mv_monthly_counts(month, source);

