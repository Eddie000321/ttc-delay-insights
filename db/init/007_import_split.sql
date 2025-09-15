\set on_error_stop on

-- Subway
DO $$
BEGIN
  BEGIN
    -- Use a staging table to tolerate extra columns in processed CSVs
    CREATE TEMP TABLE IF NOT EXISTS _stage_subway (
      date date, time text, day text, station text, line text, bound text, code text,
      min_delay numeric, min_gap numeric, vehicle numeric, source text, raw_file text, description text
    ) ON COMMIT DROP;
    TRUNCATE _stage_subway;
    COPY _stage_subway FROM '/import/subway_delays.csv'
      WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
    INSERT INTO ttc_delays_subway (
      date, time, day, station, line, bound, code, min_delay, min_gap, vehicle, raw_file
    )
    SELECT
      s.date,
      NULLIF(s.time, '')::time,
      s.day,
      s.station,
      s.line,
      s.bound,
      s.code,
      s.min_delay,
      s.min_gap,
      s.vehicle,
      s.raw_file
    FROM _stage_subway s;
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping subway import: %', SQLERRM;
  END;
END$$;

-- Streetcar
DO $$
BEGIN
  BEGIN
    CREATE TEMP TABLE IF NOT EXISTS _stage_streetcar (
      date date, time text, day text, station text, line text, bound text, code text,
      min_delay numeric, min_gap numeric, vehicle numeric, source text, raw_file text, description text
    ) ON COMMIT DROP;
    TRUNCATE _stage_streetcar;
    COPY _stage_streetcar FROM '/import/streetcar_delays.csv'
      WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
    INSERT INTO ttc_delays_streetcar (
      date, time, day, station, line, bound, code, min_delay, min_gap, vehicle, raw_file
    )
    SELECT
      s.date,
      NULLIF(s.time, '')::time,
      s.day,
      s.station,
      s.line,
      s.bound,
      s.code,
      s.min_delay,
      s.min_gap,
      s.vehicle,
      s.raw_file
    FROM _stage_streetcar s;
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping streetcar import: %', SQLERRM;
  END;
END$$;

-- Bus
DO $$
BEGIN
  BEGIN
    CREATE TEMP TABLE IF NOT EXISTS _stage_bus (
      date date, time text, day text, station text, line text, bound text, code text,
      min_delay numeric, min_gap numeric, vehicle numeric, source text, raw_file text, description text
    ) ON COMMIT DROP;
    TRUNCATE _stage_bus;
    COPY _stage_bus FROM '/import/bus_delays.csv'
      WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
    INSERT INTO ttc_delays_bus (
      date, time, day, station, line, bound, code, min_delay, min_gap, vehicle, raw_file
    )
    SELECT
      s.date,
      NULLIF(s.time, '')::time,
      s.day,
      s.station,
      s.line,
      s.bound,
      s.code,
      s.min_delay,
      s.min_gap,
      s.vehicle,
      s.raw_file
    FROM _stage_bus s;
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping bus import: %', SQLERRM;
  END;
END$$;
