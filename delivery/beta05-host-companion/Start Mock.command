#!/bin/zsh
set -eu
BASE="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
cd "$BASE"
exec python3 -B "$BASE/pilot/betaworkbench05/companion.py" start --mode mock
