-- Import per-mode CSVs into split tables when present
\set on_error_stop on

-- Subway
DO $$
BEGIN
  BEGIN
    COPY ttc_delays_subway (
      date, time, day, station, line, bound, code,
      min_delay, min_gap, vehicle, raw_file
    )
    FROM '/import/subway_delays.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping subway import: %', SQLERRM;
  END;
END$$;

-- Streetcar
DO $$
BEGIN
  BEGIN
    COPY ttc_delays_streetcar (
      date, time, day, station, line, bound, code,
      min_delay, min_gap, vehicle, raw_file
    )
    FROM '/import/streetcar_delays.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping streetcar import: %', SQLERRM;
  END;
END$$;

-- Bus
DO $$
BEGIN
  BEGIN
    COPY ttc_delays_bus (
      date, time, day, station, line, bound, code,
      min_delay, min_gap, vehicle, raw_file
    )
    FROM '/import/bus_delays.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping bus import: %', SQLERRM;
  END;
END$$;

