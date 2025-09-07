-- Import unified code dictionary CSV if present
-- Note: ensure ETL wrote /import/codes_all.csv
\set on_error_stop on

DO $$
BEGIN
  -- Attempt COPY; if file is missing, ignore gracefully via exception block
  BEGIN
    COPY ttc_code_dictionary (source, code, description)
    FROM '/import/codes_all.csv'
    WITH (
      FORMAT csv,
      HEADER true,
      DELIMITER ',',
      QUOTE '"',
      ESCAPE '"',
      NULL ''
    );
  EXCEPTION WHEN others THEN
    -- Missing file or other issue; proceed without hard failure for bootstrap
    RAISE NOTICE 'Skipping code dictionary import: %', SQLERRM;
  END;
END$$;

