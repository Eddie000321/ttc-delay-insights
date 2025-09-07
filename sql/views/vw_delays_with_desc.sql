-- Fact rows with resolved description from dictionary (prefers dictionary)
CREATE OR REPLACE VIEW vw_delays_with_desc AS
SELECT
  d.id,
  d.date,
  d.time,
  d.day,
  d.station,
  d.line,
  d.bound,
  d.code,
  d.min_delay,
  d.min_gap,
  d.vehicle,
  d.source,
  d.raw_file,
  COALESCE(cd.description, d.description) AS description_final
FROM ttc_delays d
LEFT JOIN ttc_code_dictionary cd
  ON cd.source = d.source AND cd.code = d.code;

