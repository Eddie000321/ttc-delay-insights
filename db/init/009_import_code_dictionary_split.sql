-- Import per-mode code dictionaries when present
\set on_error_stop on

-- Subway
DO $$
BEGIN
  BEGIN
    -- Tolerate an extra leading 'source' column in processed file
    CREATE TEMP TABLE IF NOT EXISTS _codes_stage_subway (
      source text, code text, description text
    ) ON COMMIT DROP;
    TRUNCATE _codes_stage_subway;
    COPY _codes_stage_subway FROM '/import/codes_subway.csv'
      WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
    INSERT INTO ttc_code_dictionary_subway (code, description)
    SELECT code, description FROM _codes_stage_subway WHERE code IS NOT NULL;
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping subway code dictionary import: %', SQLERRM;
  END;
END$$;

-- Streetcar
DO $$
BEGIN
  BEGIN
    CREATE TEMP TABLE IF NOT EXISTS _codes_stage_streetcar (
      source text, code text, description text
    ) ON COMMIT DROP;
    TRUNCATE _codes_stage_streetcar;
    COPY _codes_stage_streetcar FROM '/import/codes_streetcar.csv'
      WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
    INSERT INTO ttc_code_dictionary_streetcar (code, description)
    SELECT code, description FROM _codes_stage_streetcar WHERE code IS NOT NULL;
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping streetcar code dictionary import: %', SQLERRM;
  END;
END$$;

-- Bus
DO $$
BEGIN
  BEGIN
    CREATE TEMP TABLE IF NOT EXISTS _codes_stage_bus (
      source text, code text, description text
    ) ON COMMIT DROP;
    TRUNCATE _codes_stage_bus;
    COPY _codes_stage_bus FROM '/import/codes_bus.csv'
      WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
    INSERT INTO ttc_code_dictionary_bus (code, description)
    SELECT code, description FROM _codes_stage_bus WHERE code IS NOT NULL;
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping bus code dictionary import: %', SQLERRM;
  END;
END$$;
