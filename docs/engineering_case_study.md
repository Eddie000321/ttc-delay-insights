# TTC Delay ETL Engineering Case Study

## Problem

TTC bus, subway, and streetcar files use different column labels and value formats. A single database and dashboard contract therefore cannot safely consume the raw spreadsheets directly. Delay codes are also mode-specific, so joining every mode to one undifferentiated dictionary can attach the wrong meaning.

## Decision

The ETL maps source variants into 12 ordered standard columns, records `source` and `raw_file` provenance, normalizes times and directions, and preserves invalid numeric values as null rather than silently replacing them with zero. It drops rows that cannot identify both a date and station, sorts accepted rows deterministically, writes per-mode and unified CSV outputs, and keeps code dictionaries scoped by mode.

Network-free contract tests build temporary CSV inputs and exercise the same `process_mode` path used by the ETL. They pin a reviewed output snapshot, compare repeated executions, and assert required columns, allowed directions, non-negative durations, source identity, and relative provenance paths.

## Verification

- `/opt/anaconda3/bin/python3 -m unittest discover -s tests -v` passed all 5 tests during the 2026-07-09 audit. The suite exercises normalization plus the snapshot, repeatability, and data-contract checks without network or PostgreSQL access.
- The snapshot proves that alternate source headers, numeric/Excel-style times, trimming, code joins, sorting, invalid-negative handling, and rejection of a row without a date remain observable behaviors.
- An isolated temporary copy of `web/` passed `npm ci`, `npm run build`, and `npm audit --audit-level=high`; Vite transformed 28 modules and npm reported 0 vulnerabilities. The isolated run avoided changing the repository's existing `node_modules` deletion state.
- `/opt/anaconda3/bin/ruff check etl_scripts api tests analysis` and Python bytecode compilation provide network-free static checks for the configured Python code.

## Limits

The contract fixture uses CSV, not Excel, and does not validate a live PostgreSQL load, API response, or dashboard rendering. It checks deterministic transformation for identical inputs; it does not create a stable natural event identifier or deduplicate identical incidents across source files. The current ETL logs and skips unreadable files, so production monitoring should make skipped-file counts explicit.

## Learning

Data reliability depends on defining what may be normalized, what must remain unknown, and how every row can be traced back to its input. Small deterministic fixtures make those decisions reviewable without depending on the network, a database, or a large raw-data refresh.
