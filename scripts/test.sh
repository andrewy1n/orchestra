#!/bin/sh
set -e
cd "$(dirname "$0")/.."
run() { uv run -q --no-project --with pytest --with pytest-xdist --with textual python -m pytest -q -p no:cacheprovider "$@"; }
run -n 4 --confcutdir=tests/canon tests/canon
run -n 4 --confcutdir=tests/tuner tests/tuner
run -n 4 tests --ignore=tests/canon --ignore=tests/tuner
run tests --ignore=tests/canon --ignore=tests/tuner -m tmux
