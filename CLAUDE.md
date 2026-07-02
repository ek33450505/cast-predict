# cast-predict

Telemetry-driven dispatch prediction over `cast.db`. Extracted from the [claude-agent-team](https://github.com/ek33450505/claude-agent-team) flagship's `cast predict` command (was an inline python heredoc in `bin/cast`).

## Layout

- `bin/cast-predict` — bash launcher: `version` / `help`, else pass-through to the engine.
- `scripts/cast-predict.py` — the prediction engine. Stdlib only, argparse CLI, opens `cast.db` `mode=ro`.
- `install.sh` / `uninstall.sh` — launcher into `~/.local/bin`, script into `~/.local/lib/cast-predict`.
- `tests/cast-predict.bats` — isolated-temp-HOME BATS suite.

## Invariants (do not break)

- **Read-only.** `cast.db` opened `mode=ro`. Never add a write path.
- **Parameterized SQL.** Keywords/limits flow through bound `?` params — never interpolate user text into SQL. `IN (...)` lists use placeholder expansion.
- **Guard optional tables.** `dispatch_decisions` / `incidents` are PRAGMA-guarded + try/except — a partial schema degrades to an empty section, never a crash.
- **Honest degradation.** No matching history → clear "cannot predict", never a fabricated number.
- **Stdlib only. Local-only.** No `pip install`, no network.
- **No PII in the repo.** Docs/tests use `~/` / `/Users/you/` placeholders and synthetic sample data — never real home paths, session IDs, or `cast.db` contents.

## Query logic (preserved from the flagship)

1. **Cost** — keyword-score sessions via `routing_events.prompt_preview`; aggregate matched sessions' `agent_runs.cost_usd` (median/mean/min/max via `statistics`).
2. **Agents** — group matched sessions' `agent_runs` by agent (runs, `%` DONE, avg cost); plus a `dispatch_decisions` signal.
3. **Incidents** — `LIKE` match on `incidents.problem_summary` / `fix_summary`.

## Test

```bash
bats tests/        # isolated temp HOME
bash -n bin/cast-predict install.sh uninstall.sh
ruff check scripts/
```
