#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

check="$ROOT/skills/check/SKILL.md"
ship="$ROOT/skills/check/references/mode-ship.md"
think="$ROOT/skills/think/SKILL.md"
ui="$ROOT/skills/ui/SKILL.md"
screenshot="$ROOT/skills/ui/references/mode-screenshot-iteration.md"
design="$ROOT/skills/ui/references/design-reference.md"
health="$ROOT/skills/health/references/maintainability-findings.md"
reply="$ROOT/skills/write/references/mode-public-reply.md"

grep -q 'All local or uncommitted changes' "$check"
grep -q 'the old verdict expires' "$check"
grep -q 'explicitly authorized chain' "$ship"
grep -q 'Entity delta: +N / -N' "$think"
grep -q 'Always-on bans for every mode' "$ui"
grep -q 'freeze a minimal visual matrix' "$screenshot"
grep -q 'audit prompts, not automatic implementation scope' "$design"
grep -q 'Independent recurrence' "$health"
grep -q 'Default to one paragraph and one or two sentences' "$reply"
grep -q 'After posting or editing, re-read the comment body' "$reply"

echo "behavior contracts smoke: ok"
