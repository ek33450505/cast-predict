# cast-predict

**Predict a task before you run it — from your own history.** cast-predict reads your local Claude Code execution record (`cast.db`) and, for a task description, tells you what similar past tasks *actually* cost, which agents handled them well, and what related incidents to watch for.

It's telemetry-driven, not a guess: it keyword-matches your past sessions, aggregates their real agent-run costs, and ranks the agents that worked.

```
$ cast-predict "add a BATS test for the install script"

predict: 'add a BATS test for the install script'
Keywords: add, bats, test, install, script

── Cost Prediction ──────────────────────────────────────────────────────
Tasks like this: ≈ $0.42 median  (mean $0.55, range $0.11–$1.30) over 6 similar sessions

── Suggested Agents ─────────────────────────────────────────────────────
  Suggested: bash-specialist        (5 runs on similar tasks, 100% DONE, ≈$0.31 avg)
  Suggested: code-reviewer          (4 runs on similar tasks, 100% DONE, ≈$0.08 avg)

── Related Incidents ────────────────────────────────────────────────────
  BATS test touched real $HOME and wiped fixtures  [a1b2c3d4]
    → isolate via setup_temp_home/teardown_temp_home
```

- **Strictly read-only.** `cast.db` is opened `mode=ro`.
- **Local-only.** No network, no telemetry. Your history never leaves your machine.
- **Zero dependencies.** Python 3 stdlib only — no `pip install`.
- **Degrades gracefully.** Missing/empty tables produce an honest "cannot predict", never a crash.

Works **without** the full CAST framework. Point it at any `cast.db`.

## Install (Homebrew)

```bash
brew tap ek33450505/cast-predict && brew install cast-predict
```

## Manual install

```bash
git clone https://github.com/ek33450505/cast-predict.git
cd cast-predict
bash install.sh
```

`install.sh` copies the `cast-predict` launcher into `~/.local/bin` and the script into `~/.local/lib/cast-predict/`. Idempotent — safe to re-run.

## Usage

```bash
cast-predict "<task description>"           # predict cost, agents, incidents
cast-predict "<task description>" --limit 8 # show up to 8 agents / incidents (default 5)
cast-predict "<task description>" --json    # machine-readable output
cast-predict version
```

### What it computes

| Section | How |
|---|---|
| **Cost prediction** | Finds past sessions whose routing prompts share keywords with your task, then aggregates their real `agent_runs` cost → median, mean, and range. Flags low confidence when few sessions match. |
| **Suggested agents** | Which agents ran on those similar sessions — run count, `%` that reached `DONE`, and average cost — plus any `dispatch_decisions` signal. |
| **Related incidents** | Past incidents whose problem/fix summaries match your task's keywords, with the related commit. |

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `CAST_DB_PATH` | `~/.claude/cast.db` | Path to the record database (opened read-only) |

`--db PATH` overrides it for a single run.

## Security

- Opens `cast.db` read-only (`mode=ro`) — cast-predict never writes.
- All queries are parameterized; the task's keywords flow through bound parameters, never string-interpolated into SQL.
- No network, no secrets. Local-only.

See [SECURITY.md](SECURITY.md).

## Requirements

- **Python 3** (stdlib only)
- **sqlite3**
- A `cast.db` with some history (created by [claude-agent-team](https://github.com/ek33450505/claude-agent-team) or any CAST tool). With an empty record it honestly reports it can't predict yet.

## Part of the CAST ecosystem

Extracted from [claude-agent-team](https://github.com/ek33450505/claude-agent-team)'s `cast predict` command.

<!-- ECOSYSTEM_START -->
| Repo | Description | Install |
|---|---|---|
| [claude-agent-team](https://github.com/ek33450505/claude-agent-team) | The CAST flagship — the local, inspectable, tamper-evident record of what your agents did. | `git clone` |
<!-- ECOSYSTEM_END -->

## License

[MIT](LICENSE) © Edward Kubiak
