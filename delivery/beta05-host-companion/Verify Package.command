#!/bin/zsh
set -eu
BASE="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
if (( $# > 0 )); then
  FILE="$1"
else
  read -r 'FILE?Dán đường dẫn gói SAF JSON (không thêm dấu nháy): '
fi
cd "$BASE"
exec node "$BASE/delivery/beta05-host-companion/verify-package.mjs" "$FILE"
