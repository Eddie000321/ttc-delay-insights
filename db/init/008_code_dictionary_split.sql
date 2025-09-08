-- Per-mode code dictionary tables (preferred over unified)
CREATE TABLE IF NOT EXISTS ttc_code_dictionary_subway (
  code        text PRIMARY KEY,
  description text
);

CREATE TABLE IF NOT EXISTS ttc_code_dictionary_streetcar (
  code        text PRIMARY KEY,
  description text
);

CREATE TABLE IF NOT EXISTS ttc_code_dictionary_bus (
  code        text PRIMARY KEY,
  description text
);

