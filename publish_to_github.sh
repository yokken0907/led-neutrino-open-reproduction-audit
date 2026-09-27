#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
REMOTE="https://github.com/yokken0907/led-neutrino-open-reproduction-audit.git"
command -v git >/dev/null || { echo "git is required" >&2; exit 2; }
if [[ ! -d .git ]]; then
  git init -b main
fi
git config user.name >/dev/null 2>&1 || git config user.name "Keiji Yoshimura"
git config user.email >/dev/null 2>&1 || git config user.email "yokken0907@users.noreply.github.com"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE"
else
  git remote add origin "$REMOTE"
fi
git add -A
git commit -m "Publish D27C reproducibility audit" || true
git branch -M main
git push -u origin main
printf '
Published: https://github.com/yokken0907/led-neutrino-open-reproduction-audit
'
