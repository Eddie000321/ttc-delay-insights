-- Split-by-mode fact tables (primary usage)
CREATE TABLE IF NOT EXISTS ttc_delays_subway (
  id          bigserial PRIMARY KEY,
  date        date        NOT NULL,
  time        time,
  day         text,
  station     text        NOT NULL,
  line        text,
  bound       text,
  code        text,
  min_delay   numeric,
  min_gap     numeric,
  vehicle     numeric,
  raw_file    text,
  CONSTRAINT ttc_delays_subway_ck_delay_nonneg CHECK ((min_delay IS NULL OR min_delay >= 0)),
  CONSTRAINT ttc_delays_subway_ck_gap_nonneg   CHECK ((min_gap IS NULL OR min_gap >= 0)),
  CONSTRAINT ttc_delays_subway_ck_bound        CHECK (bound IS NULL OR bound IN ('N','E','S','W'))
);

CREATE TABLE IF NOT EXISTS ttc_delays_streetcar (
  id          bigserial PRIMARY KEY,
  date        date        NOT NULL,
  time        time,
  day         text,
  station     text        NOT NULL,
  line        text,
  bound       text,
  code        text,
  min_delay   numeric,
  min_gap     numeric,
  vehicle     numeric,
  raw_file    text,
  CONSTRAINT ttc_delays_streetcar_ck_delay_nonneg CHECK ((min_delay IS NULL OR min_delay >= 0)),
  CONSTRAINT ttc_delays_streetcar_ck_gap_nonneg   CHECK ((min_gap IS NULL OR min_gap >= 0)),
  CONSTRAINT ttc_delays_streetcar_ck_bound        CHECK (bound IS NULL OR bound IN ('N','E','S','W'))
);

CREATE TABLE IF NOT EXISTS ttc_delays_bus (
  id          bigserial PRIMARY KEY,
  date        date        NOT NULL,
  time        time,
  day         text,
  station     text        NOT NULL,
  line        text,
  bound       text,
  code        text,
  min_delay   numeric,
  min_gap     numeric,
  vehicle     numeric,
  raw_file    text,
  CONSTRAINT ttc_delays_bus_ck_delay_nonneg CHECK ((min_delay IS NULL OR min_delay >= 0)),
  CONSTRAINT ttc_delays_bus_ck_gap_nonneg   CHECK ((min_gap IS NULL OR min_gap >= 0)),
  CONSTRAINT ttc_delays_bus_ck_bound        CHECK (bound IS NULL OR bound IN ('N','E','S','W'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_subway_date    ON ttc_delays_subway(date);
CREATE INDEX IF NOT EXISTS idx_subway_station ON ttc_delays_subway(station);
CREATE INDEX IF NOT EXISTS idx_subway_line    ON ttc_delays_subway(line);

CREATE INDEX IF NOT EXISTS idx_streetcar_date    ON ttc_delays_streetcar(date);
CREATE INDEX IF NOT EXISTS idx_streetcar_station ON ttc_delays_streetcar(station);
CREATE INDEX IF NOT EXISTS idx_streetcar_line    ON ttc_delays_streetcar(line);

CREATE INDEX IF NOT EXISTS idx_bus_date    ON ttc_delays_bus(date);
CREATE INDEX IF NOT EXISTS idx_bus_station ON ttc_delays_bus(station);
CREATE INDEX IF NOT EXISTS idx_bus_line    ON ttc_delays_bus(line);

