-- Base table for TTC delays
CREATE TABLE IF NOT EXISTS ttc_delays (
  date        date,
  time        time,
  day         text,
  station     text,
  line        text,
  bound       text,
  code        text,
  min_delay   numeric,
  min_gap     numeric,
  vehicle     numeric,
  source      text,
  raw_file    text,
  description text
);

