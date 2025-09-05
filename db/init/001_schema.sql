CREATE TABLE IF NOT EXISTS ttc_delays (
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
  source      text        NOT NULL,
  raw_file    text,
  description text,
  CONSTRAINT ttc_delays_ck_delay_nonneg CHECK (
    (min_delay IS NULL OR min_delay >= 0)
  ),
  CONSTRAINT ttc_delays_ck_gap_nonneg CHECK (
    (min_gap IS NULL OR min_gap >= 0)
  ),
  CONSTRAINT ttc_delays_ck_bound CHECK (
    bound IS NULL OR bound IN ('N','E','S','W')
  )
);
