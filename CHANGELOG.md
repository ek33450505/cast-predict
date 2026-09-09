# Changelog

## [0.1.1] — 2026-09-09

Maintenance release. No behaviour change to prediction output.

### Fixed
- `scripts/cast-predict.py` carried a shebang but was not executable (`EXE001`).
- CI installed `ruff` unpinned, so the gate floated to whatever `ruff` released
  most recently. `ruff` 0.16.x enabled new default rules this repo's code
  predates, meaning CI would have failed on `main` for a reason unrelated to any
  change. Pinned to `0.15.14`, mirroring `claude-agent-team`'s `security-scan.yml`.

### Verified
- Queries were live-probed against a copy of a current `cast.db`: all tables and
  columns `cast-predict.py` reads still exist, and prediction output is correct.

## [0.1.0] — 2026-07-01

Initial release. Extracted from [claude-agent-team](https://github.com/ek33450505/claude-agent-team) v9's `cast predict` command.

### Added
- Standalone `cast-predict` launcher + `scripts/cast-predict.py` (argparse CLI):
  - `cast-predict "<task>" [--limit N] [--json] [--db PATH]`
  - **Cost prediction** — keyword-matches past sessions via `routing_events.prompt_preview`, aggregates their `agent_runs` cost (median / mean / min / max), flags low confidence on few matches
  - **Suggested agents** — agents that ran on similar sessions (runs, `%` DONE, avg cost) + `dispatch_decisions` signal
  - **Related incidents** — `incidents` whose problem/fix summaries match the task keywords, with related commit
  - Text or `--json` output; graceful degradation when tables are absent/empty
- `cast.db` opened read-only (`mode=ro`); all queries parameterized
- Idempotent `install.sh` / `uninstall.sh` — launcher into `~/.local/bin`, script into `~/.local/lib/cast-predict`
- `CAST_DB_PATH` env override + `--db` flag

### Notes
- Python 3 stdlib only — no `pip install`
- Local-only: no network, no telemetry
