-- Import per-mode code dictionaries when present
\set on_error_stop on

-- Subway
DO $$
BEGIN
  BEGIN
    COPY ttc_code_dictionary_subway (code, description)
    FROM '/import/codes_subway.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping subway code dictionary import: %', SQLERRM;
  END;
END$$;

-- Streetcar
DO $$
BEGIN
  BEGIN
    COPY ttc_code_dictionary_streetcar (code, description)
    FROM '/import/codes_streetcar.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping streetcar code dictionary import: %', SQLERRM;
  END;
END$$;

-- Bus
DO $$
BEGIN
  BEGIN
    COPY ttc_code_dictionary_bus (code, description)
    FROM '/import/codes_bus.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping bus code dictionary import: %', SQLERRM;
  END;
END$$;

