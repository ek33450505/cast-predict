# Security Policy

## Supported Versions

| Version | Support Status |
|---|---|
| 0.1.x | Full support — security fixes backported |
| < 0.1 | No longer supported |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Report privately using [GitHub Security Advisories](https://github.com/ek33450505/cast-predict/security/advisories/new).

### What to Include

- **Version** — `cast-predict version`
- **Operating system** — `sw_vers` (macOS) or `lsb_release -a` (Linux)
- **Which surface** — e.g., the cost-prediction query, `--json` output
- **Steps to reproduce** — minimal, clear reproduction steps
- **Impact** — what an attacker could do

### Response Timeline

| Severity | Acknowledgment | Fix Target |
|---|---|---|
| Critical | 48 hours | 14 days |
| High | 48 hours | 30 days |
| Medium / Low | 5 business days | Next release |

## Security Design Notes

cast-predict is a read-only analytics CLI. Key design decisions:

- **Read-only** — `cast.db` is opened with the SQLite URI `mode=ro`. cast-predict never writes to the record.
- **Parameterized queries** — the task's extracted keywords and limits flow through bound `?` parameters. `LIKE` filters and `IN (...)` lists are built with placeholders, never by interpolating user text into SQL.
- **Defensive table access** — every optional table (`dispatch_decisions`, `incidents`) is `PRAGMA`-guarded and wrapped in try/except, so a missing or partial schema degrades to an empty section rather than a crash.
- **Bounded** — the result limit is an integer flag; keyword extraction strips to a simple alphanumeric token set.
- **No network, no secrets** — cast-predict makes no external requests and handles no credentials.

## Out of Scope

- Vulnerabilities in the Claude API or Anthropic services — report to [Anthropic](https://www.anthropic.com/security)
- Vulnerabilities in third-party tools (bash, Python, sqlite3, BATS)
- The contents of `~/.claude/cast.db` — a user-controlled input the tool only reads

## Trust Model

cast-predict assumes the user controls `~/.claude/`, and that the `sqlite3` library and Python interpreter are trustworthy. `cast.db` is trusted input, read only. cast-predict uses stdlib only (`sqlite3`, `json`, `os`, `re`, `sys`, `argparse`, `statistics`).
