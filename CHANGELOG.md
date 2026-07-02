# Changelog

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
