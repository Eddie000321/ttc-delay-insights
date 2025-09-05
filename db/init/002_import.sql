-- Import unified CSV from mounted path
COPY ttc_delays (
  date, time, day, station, line, bound, code,
  min_delay, min_gap, vehicle, source, raw_file, description
)
FROM '/import/ttc_delays.csv'
WITH (
  FORMAT csv,
  HEADER true,
  DELIMITER ',',
  QUOTE '"',
  ESCAPE '"',
  NULL ''
);

