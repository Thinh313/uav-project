#!/bin/zsh
set -eu
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
AERIS_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
AERIS_NODE="${AERIS_NODE:-/usr/local/bin/node}"
if [[ ! -x "$AERIS_NODE" ]]; then
  print 'Không tìm thấy Node hiện có. Đặt AERIS_NODE tới runtime Node được duyệt.'
  exit 1
fi
cd -- "$AERIS_ROOT"
print 'AERIS Debrief: http://127.0.0.1:8897'
print 'Chỉ xem hồ sơ. Ctrl+C để dừng. Tự đóng sau 30 phút.'
exec "$AERIS_NODE" pilot/coach01/server.mjs
