CREATE INDEX IF NOT EXISTS idx_ttc_delays_date ON ttc_delays(date);
CREATE INDEX IF NOT EXISTS idx_ttc_delays_line ON ttc_delays(line);
CREATE INDEX IF NOT EXISTS idx_ttc_delays_station ON ttc_delays(station);
CREATE INDEX IF NOT EXISTS idx_ttc_delays_source_date ON ttc_delays(source, date);
