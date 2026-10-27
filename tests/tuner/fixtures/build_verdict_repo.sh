#!/usr/bin/env bash
# Materialize tests/fixtures/verdict-repo as a two-commit git subject (red then green).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FIXTURE="$ROOT/tests/fixtures/verdict-repo"
cd "$FIXTURE"

if [[ ! -f app.py || ! -f app.red.py || ! -f tests/test_widget.py || ! -f .affidavit/manifest.json ]]; then
  echo "build_verdict_repo: missing templates under $FIXTURE" >&2
  exit 1
fi

rm -rf .git
git init -q -b main
git config user.email "fixture@example.com"
git config user.name "fixture"
git config core.autocrlf false
git config commit.gpgsign false

# Red base: failing app
cp app.red.py app.py
git add -A
# Do not commit app.red.py as the live app — keep both files tracked
git add app.red.py app.py tests .affidavit pytest.ini
git commit -qm "fixture: red base (value=0)"

# Green head
printf 'value = 1\n' > app.py
git add app.py
git commit -qm "fixture: green head (value=1)"

echo "build_verdict_repo: ready at $FIXTURE"
echo "BASE=$(git rev-parse HEAD~1)"
echo "HEAD=$(git rev-parse HEAD)"
