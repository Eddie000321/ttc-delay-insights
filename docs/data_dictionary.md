# Data Dictionary – TTC Delay Project

This document defines the standardized columns across bus, subway, and streetcar delay datasets (CSV outputs and the PostgreSQL table).

| Column      | Type    | Description                                                             |
| ----------- | ------- | ----------------------------------------------------------------------- |
| date        | date    | Date of the delay event (YYYY-MM-DD)                                    |
| time        | time    | Time of the delay event (HH:MM or HH:MM:SS)                             |
| day         | text    | Day of week (e.g., Monday, Tuesday)                                     |
| station     | text    | Location where the delay occurred                                       |
| line        | text    | Route or line identifier (e.g., `504 KING`, `BD`)                       |
| bound       | text    | Direction of travel: one of `N`, `E`, `S`, `W` or NULL                  |
| code        | text    | Cause of delay (TTC official code list; may be NULL)                    |
| min_delay   | numeric | Minutes of actual delay (non-negative; NULL if unknown/invalid)         |
| min_gap     | numeric | Minutes between this vehicle and the previous one (non-negative/NULL)   |
| vehicle     | numeric | Vehicle identifier (car/bus/train number; numeric where applicable)     |
| source      | text    | Data source/mode: `bus`, `subway`, or `streetcar`                       |
| raw_file    | text    | Relative path of the raw file that produced the row                     |
| description | text    | Optional description joined from code list (if available; subway/streetcar) |

Notes:

- CSV outputs under `data/processed/*.csv` include these columns; `description` is present where a code-description file exists (often subway/streetcar).
- The PostgreSQL table is named `ttc_delays`.
- In the database, an internal `id bigserial` primary key exists; it is not part of the CSV outputs.
- Code values are documented in TTC’s official data catalog; unmapped or unmatched codes will have `description = NULL`.
