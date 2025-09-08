-- Views exposing fact rows with resolved descriptions per mode

CREATE OR REPLACE VIEW vw_subway_with_desc AS
SELECT
  s.*,
  d.description AS description_final
FROM ttc_delays_subway s
LEFT JOIN ttc_code_dictionary_subway d ON d.code = s.code;

CREATE OR REPLACE VIEW vw_streetcar_with_desc AS
SELECT
  s.*,
  d.description AS description_final
FROM ttc_delays_streetcar s
LEFT JOIN ttc_code_dictionary_streetcar d ON d.code = s.code;

CREATE OR REPLACE VIEW vw_bus_with_desc AS
SELECT
  s.*,
  d.description AS description_final
FROM ttc_delays_bus s
LEFT JOIN ttc_code_dictionary_bus d ON d.code = s.code;

-- Optional convenience union view (read-only convenience)
CREATE OR REPLACE VIEW vw_delays_all_with_desc AS
SELECT 'subway' AS source, * FROM vw_subway_with_desc
UNION ALL
SELECT 'streetcar' AS source, * FROM vw_streetcar_with_desc
UNION ALL
SELECT 'bus' AS source, * FROM vw_bus_with_desc;

