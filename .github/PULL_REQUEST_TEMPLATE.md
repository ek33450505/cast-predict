## Description

<!-- What does this PR change and why? -->

## Checklist

- [ ] `bash install.sh && bash uninstall.sh` round-trip clean
- [ ] BATS tests pass: `bats tests/`
- [ ] `bash -n bin/cast-predict install.sh uninstall.sh` — all syntax-check
- [ ] `cast-predict --quick` and `cast-predict --json` both work
- [ ] No writes to disk anywhere — cast-predict is strictly read-only
- [ ] No hardcoded paths — `$HOME` / `~/` used
- [ ] `CHANGELOG.md` updated for user-visible changes
