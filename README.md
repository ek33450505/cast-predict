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
**Core Framework**

| Repo | Description | Latest | Install |
|---|---|---|---|
| [claude-agent-team](https://github.com/ek33450505/claude-agent-team) | Local-first multi-agent control plane — specialist agents, quality gates, hook enforcement, and the tamper-evident cast.db execution record. | ![](https://img.shields.io/github/v/release/ek33450505/claude-agent-team?style=flat-square) | `brew tap ek33450505/cast && brew install cast` |

**Observability**

| Repo | Description | Latest | Install |
|---|---|---|---|
| [claude-code-dashboard](https://github.com/ek33450505/claude-code-dashboard) | React observability UI — sessions, agent analytics, hook health, memory browser, SQLite explorer. | ![](https://img.shields.io/github/v/release/ek33450505/claude-code-dashboard?style=flat-square) | Clone from GitHub |
| [cast-desktop](https://github.com/ek33450505/cast-desktop) | Tauri 2 native app — embedded PTY terminal, command palette, 11 dashboard views. | ![](https://img.shields.io/github/v/release/ek33450505/cast-desktop?style=flat-square) | `brew tap ek33450505/homebrew-cast-desktop && brew install cast-desktop` |

**Standalone Packages**

| Repo | Description | Latest | Install |
|---|---|---|---|
| [cast-mcp](https://github.com/ek33450505/cast-mcp) | Read-only MCP server over the Claude Code execution record (cast.db) — dispatch decisions, incidents, cost, sessions, and full-text search as 5 MCP tools + 5 resources. stdlib-only, strictly read-only. | ![](https://img.shields.io/github/v/release/ek33450505/cast-mcp?style=flat-square) | `brew tap ek33450505/cast-mcp && brew install cast-mcp` |
| [cast-ledger](https://github.com/ek33450505/cast-ledger) | Signed, hash-chained, tamper-evident session receipts for Claude Code — SHA-256-stamped audit receipts from cast.db with `--verify`, plus an optional provenance hash-chain across sessions. | ![](https://img.shields.io/github/v/release/ek33450505/cast-ledger?style=flat-square) | `brew tap ek33450505/cast-ledger && brew install cast-ledger` |
| [cast-predict](https://github.com/ek33450505/cast-predict) | Telemetry-driven dispatch prediction for Claude Code — reads cast.db to predict a task's likely cost, suggest agents, and surface related past incidents before you run it. | ![](https://img.shields.io/github/v/release/ek33450505/cast-predict?style=flat-square) | `brew tap ek33450505/cast-predict && brew install cast-predict` |
| [cast-memory](https://github.com/ek33450505/cast-memory) | Persistent agent memory for Claude Code — FTS5 full-text search, weighted relevance, temporal validity, Ollama embeddings, and weekly consolidation over cast.db. | ![](https://img.shields.io/github/v/release/ek33450505/cast-memory?style=flat-square) | `brew tap ek33450505/cast-memory && brew install cast-memory` |
| [cast-doctor](https://github.com/ek33450505/cast-doctor) | Standalone read-only health check for any Claude Code install — validates hooks, MCP config, agent frontmatter, cast.db core schema, and stale memories without the full CAST framework. | ![](https://img.shields.io/github/v/release/ek33450505/cast-doctor?style=flat-square) | `brew tap ek33450505/cast-doctor && brew install cast-doctor` |
| [cast-time](https://github.com/ek33450505/cast-time) | Gives Claude Code a clock — injects local time, timezone, and a semantic time-of-day bucket at every SessionStart. | ![](https://img.shields.io/github/v/release/ek33450505/cast-time?style=flat-square) | `brew tap ek33450505/cast-time && brew install cast-time` |
| [cast-claudes_journal](https://github.com/ek33450505/cast-claudes_journal) | Three-hook journaling for Claude Code (Stop/SessionStart/UserPromptSubmit) — maintains Claude's perspective and working memory across sessions as Obsidian-compatible markdown in ~/Documents/Claude/. | ![](https://img.shields.io/github/v/release/ek33450505/cast-claudes_journal?style=flat-square) | `brew tap ek33450505/homebrew-claudes-journal && brew install claudes-journal` |
<!-- ECOSYSTEM_END -->

## License

[MIT](LICENSE) © Edward Kubiak
