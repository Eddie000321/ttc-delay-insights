-- Code dictionary per mode
CREATE TABLE IF NOT EXISTS ttc_code_dictionary (
  source      text NOT NULL,
  code        text NOT NULL,
  description text,
  PRIMARY KEY (source, code)
);

-- Optional supporting index for code-only lookups
CREATE INDEX IF NOT EXISTS idx_ttc_code_dictionary_code ON ttc_code_dictionary(code);

