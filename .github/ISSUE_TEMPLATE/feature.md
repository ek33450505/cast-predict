---
name: Feature request
about: New diagnostic check, new flag, or behavior change
labels: enhancement
---

## What you want

<!-- New check, new flag, or behavior change -->

## Why

<!-- Use case — what problem this surfaces -->

## Proposed surface

<!-- For new checks: which path/file/db query, what threshold, what severity (ok/warn/err) -->
<!-- For new flags: usage signature -->

## Constraints to honor

- cast-predict is read-only — no writes ever
- Stdlib Python only, no PyYAML dependency
- Cross-platform (macOS + Linux), bash 3.2 compatible
