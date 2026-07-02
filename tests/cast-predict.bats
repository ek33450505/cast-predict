#!/usr/bin/env bats
# tests/cast-predict.bats — isolated BATS suite for cast-predict.
# Uses a temp HOME and a scratch cast.db — never touches the real ~/.claude.

REPO_DIR="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
CLI="$REPO_DIR/bin/cast-predict"
export CAST_PREDICT_SCRIPT="$REPO_DIR/scripts/cast-predict.py"

setup() {
  _ORIG_HOME="$HOME"
  HOME="$(mktemp -d)"
  export HOME
  mkdir -p "$HOME/.claude"
  export CAST_DB_PATH="$BATS_TEST_TMPDIR/test-predict-$$.db"
}

teardown() {
  rm -f "$CAST_DB_PATH" 2>/dev/null || true
  rm -rf "$HOME" 2>/dev/null || true
  HOME="$_ORIG_HOME"
  export HOME
}

# Helper: build a populated test db with matching history.
_make_db() {
  command -v sqlite3 >/dev/null || skip "sqlite3 not available"
  sqlite3 "$CAST_DB_PATH" "
CREATE TABLE sessions(id TEXT);
CREATE TABLE routing_events(session_id TEXT, prompt_preview TEXT);
CREATE TABLE agent_runs(session_id TEXT, agent TEXT, status TEXT, cost_usd REAL);
CREATE TABLE incidents(problem_summary TEXT, fix_summary TEXT, related_commit TEXT);
CREATE TABLE dispatch_decisions(prompt_snippet TEXT, chosen_agent TEXT, outcome TEXT);
INSERT INTO routing_events VALUES('s1','add a bats test for the installer');
INSERT INTO routing_events VALUES('s2','add a bats test suite');
INSERT INTO agent_runs VALUES('s1','bash-specialist','DONE',0.31);
INSERT INTO agent_runs VALUES('s2','bash-specialist','DONE',0.20);
INSERT INTO agent_runs VALUES('s1','code-reviewer','DONE',0.08);
INSERT INTO incidents VALUES('bats test wiped fixtures','isolate via temp HOME','a1b2c3d4');
"
}

# ── Test 1: CLI is executable ──────────────────────────────────────────────────
@test "CLI is executable" {
  [ -x "$CLI" ]
}

# ── Test 2: version subcommand ─────────────────────────────────────────────────
@test "version → status 0, outputs 'cast-predict v'" {
  run bash "$CLI" version
  [ "$status" -eq 0 ]
  [[ "$output" == *"cast-predict v"* ]]
}

# ── Test 3: help / no-arg ──────────────────────────────────────────────────────
@test "no args → status 0, outputs Usage:" {
  run bash "$CLI"
  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage:"* ]]
}

# ── Test 4: CLAUDE_SUBPROCESS guard ───────────────────────────────────────────
@test "CLAUDE_SUBPROCESS=1 → status 0, empty output" {
  run env CLAUDE_SUBPROCESS=1 bash "$CLI" "add a bats test"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── Test 5: missing db → nonzero + error message ──────────────────────────────
@test "missing db → nonzero exit + 'cast.db not found' message" {
  export CAST_DB_PATH="$BATS_TEST_TMPDIR/nonexistent-$$.db"
  run bash "$CLI" "add a bats test"
  [ "$status" -ne 0 ]
  [[ "${output}${stderr:-}" == *"cast.db not found"* ]] || [[ "$(cat /dev/stderr 2>/dev/null)" == *"cast.db not found"* ]] || true
  # Check combined stdout+stderr via the run output (bats captures stderr in $output for bash invocations)
  [[ "$output" == *"cast.db not found"* ]] || [[ "${lines[*]}" == *"cast.db not found"* ]]
}

# ── Test 6: prediction text output ────────────────────────────────────────────
@test "prediction: output contains key sections" {
  _make_db
  run bash "$CLI" "add a bats test"
  [ "$status" -eq 0 ]
  [[ "$output" == *"predict:"* ]]
  [[ "$output" == *"Keywords:"* ]]
  [[ "$output" == *"Cost Prediction"* ]]
  [[ "$output" == *"Suggested Agents"* ]]
}

# ── Test 7: suggests bash-specialist ──────────────────────────────────────────
@test "prediction: suggests bash-specialist agent" {
  _make_db
  run bash "$CLI" "add a bats test"
  [ "$status" -eq 0 ]
  [[ "$output" == *"bash-specialist"* ]]
}

# ── Test 8: related incident surfaced ─────────────────────────────────────────
@test "related incident: surfaces fixture incident text" {
  _make_db
  run bash "$CLI" "bats test fixtures"
  [ "$status" -eq 0 ]
  [[ "$output" == *"isolate via temp HOME"* ]] || [[ "$output" == *"bats test wiped fixtures"* ]]
}

# ── Test 9: --json output is valid JSON with required keys ────────────────────
@test "--json: valid JSON with required top-level keys" {
  _make_db
  run bash "$CLI" "add a bats test" --json
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert 'task' in d, 'missing task'
assert 'cost_prediction' in d, 'missing cost_prediction'
assert 'suggested_agents' in d, 'missing suggested_agents'
assert 'related_incidents' in d, 'missing related_incidents'
"
}

# ── Test 10: empty-db / no-keyword-match is graceful ─────────────────────────
@test "no keyword match → status 0, graceful 'cannot predict' or similar" {
  command -v sqlite3 >/dev/null || skip "sqlite3 not available"
  sqlite3 "$CAST_DB_PATH" "
CREATE TABLE sessions(id TEXT);
CREATE TABLE routing_events(session_id TEXT, prompt_preview TEXT);
CREATE TABLE agent_runs(session_id TEXT, agent TEXT, status TEXT, cost_usd REAL);
CREATE TABLE incidents(problem_summary TEXT, fix_summary TEXT, related_commit TEXT);
CREATE TABLE dispatch_decisions(prompt_snippet TEXT, chosen_agent TEXT, outcome TEXT);
"
  run bash "$CLI" "zzqqxx nonsense"
  [ "$status" -eq 0 ]
  [[ "$output" == *"cannot predict"* ]] || [[ "$output" == *"No similar tasks"* ]] || [[ "$output" == *"No usable keywords"* ]]
}

# ── Test 11: --limit smoke ────────────────────────────────────────────────────
@test "--limit 1 → status 0 (smoke)" {
  _make_db
  run bash "$CLI" "add a bats test" --limit 1
  [ "$status" -eq 0 ]
}

# ── Test 12: bin/cast-predict passes bash -n ──────────────────────────────────
@test "bin/cast-predict: bash -n syntax check" {
  run bash -n "$REPO_DIR/bin/cast-predict"
  [ "$status" -eq 0 ]
}

# ── Test 13: install.sh passes bash -n ───────────────────────────────────────
@test "install.sh: bash -n syntax check" {
  run bash -n "$REPO_DIR/install.sh"
  [ "$status" -eq 0 ]
}

# ── Test 14: uninstall.sh passes bash -n ─────────────────────────────────────
@test "uninstall.sh: bash -n syntax check" {
  run bash -n "$REPO_DIR/uninstall.sh"
  [ "$status" -eq 0 ]
}
