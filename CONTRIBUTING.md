# Contributing to cast-predict

Thanks for your interest! cast-predict reads `cast.db` to predict a task's likely cost, suggest agents, and surface related incidents. Contributions that improve the matching heuristics, add prediction signals, or harden cross-platform support are welcome.

## Prerequisites

- **bash** + **python3** — both ship with macOS / standard Linux
- **sqlite3** — required at runtime
- **BATS** — `brew install bats-core` (macOS) or `apt-get install bats` (Ubuntu)
- **ruff** (optional) — `pip install ruff` or `brew install ruff`

Stdlib Python only — no third-party dependencies.

## Quick Start

```bash
git clone https://github.com/ek33450505/cast-predict
cd cast-predict
bash install.sh
cast-predict "add a test"
```

`install.sh` is idempotent — safe to re-run.

## Layout

- `bin/cast-predict` — bash launcher (`version` / `help`, else pass-through to the script).
- `scripts/cast-predict.py` — the prediction engine (read-only, `mode=ro`, argparse CLI).

## How to Modify

- **Stay read-only.** The engine opens `cast.db` `mode=ro` and must never write.
- **Parameterize everything.** Keyword and limit inputs flow through bound `?` parameters. Never interpolate user text into SQL.
- **Guard optional tables.** Wrap every non-core table access (`dispatch_decisions`, `incidents`) in a `PRAGMA`/try-except so a partial schema degrades gracefully.
- **Honest degradation.** With no matching history, print a clear "cannot predict" — never a fabricated number.

## PR Checklist

- [ ] `bash install.sh && bash uninstall.sh` round-trip clean
- [ ] BATS tests pass: `bats tests/`
- [ ] `bash -n bin/cast-predict install.sh uninstall.sh` — all syntax-check
- [ ] `ruff check scripts/` clean (if ruff installed)
- [ ] `--json` output is valid JSON; empty-db run degrades cleanly
- [ ] No writes to `cast.db`
- [ ] No hardcoded `/Users/<name>/` paths — use `$HOME` / `~/`
- [ ] `CHANGELOG.md` updated for user-visible changes

## Code Style

- All scripts: `set -euo pipefail`
- Quote variable expansions: `"$var"`
- Use `[[ ]]` for conditionals, not `[ ]`
- ShellCheck clean — no warnings
- Python: stdlib only, `ruff`-clean

## Reporting issues

Use the GitHub issue templates under `.github/ISSUE_TEMPLATE/`. For security issues, see [SECURITY.md](SECURITY.md) — do not open a public issue.
