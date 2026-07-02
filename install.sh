#!/bin/bash
# install.sh — cast-predict installer.
# Copies the launcher into ~/.local/bin and the engine into ~/.local/lib/cast-predict.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CP_VERSION="$(cat "$REPO_DIR/VERSION" 2>/dev/null || echo unknown)"

if [ -t 1 ] && [ "${TERM:-}" != "dumb" ]; then
  C_BOLD='\033[1m'; C_GREEN='\033[0;32m'; C_YELLOW='\033[0;33m'
  C_RED='\033[0;31m'; C_RESET='\033[0m'
else
  C_BOLD='' C_GREEN='' C_YELLOW='' C_RED='' C_RESET=''
fi

_ok()   { printf "${C_GREEN}  [ok]${C_RESET} %s\n" "$*"; }
_warn() { printf "${C_YELLOW}  [warn]${C_RESET} %s\n" "$*" >&2; }
_fail() { printf "${C_RED}  [fail]${C_RESET} %s\n" "$*" >&2; exit 1; }
_step() { printf "\n${C_BOLD}%s${C_RESET}\n" "$*"; }

printf "\n${C_BOLD}cast-predict v${CP_VERSION} installer${C_RESET}\n"
printf "═════════════════════════════════════════════\n"
printf "  Predict a task's cost / agents / incidents from your cast.db.\n\n"

_step "Checking prerequisites..."
command -v python3 >/dev/null || _fail "python3 not found"
command -v sqlite3 >/dev/null || _warn "sqlite3 not found — runtime queries need it"
_ok "python3 available"

_step "Installing engine + launcher..."
BIN_TARGET="${CAST_BIN_DIR:-$HOME/.local/bin}"
LIB_TARGET="${CAST_LIB_DIR:-$HOME/.local/lib/cast-predict}"
mkdir -p "$BIN_TARGET" "$LIB_TARGET"
cp "$REPO_DIR/scripts/cast-predict.py" "$LIB_TARGET/cast-predict.py"
cp "$REPO_DIR/VERSION" "$LIB_TARGET/VERSION"
cp "$REPO_DIR/bin/cast-predict" "$BIN_TARGET/cast-predict"
chmod 755 "$BIN_TARGET/cast-predict"
_ok "cast-predict.py → $LIB_TARGET/cast-predict.py"
_ok "cast-predict → $BIN_TARGET/cast-predict"

if [[ ":$PATH:" != *":$BIN_TARGET:"* ]]; then
  _warn "$BIN_TARGET is not on your PATH — add it to your shell rc to use \`cast-predict\` directly."
fi

printf "\n${C_BOLD}═════════════════════════════════════════════${C_RESET}\n"
printf "${C_GREEN}cast-predict v${CP_VERSION} installed.${C_RESET}\n\n"
printf "${C_BOLD}Try it:${C_RESET}\n"
printf "  cast-predict \"add a BATS test\"\n\n"
