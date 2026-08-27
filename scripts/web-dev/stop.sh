#!/usr/bin/env bash
# Stops the aiwb GUI server started by start.sh. Patterned after
# litrpg/scripts/web-dev/stop.sh.
#
# Usage: scripts/web-dev/stop.sh [STATE_DIR]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  cat <<EOF
Usage: $0 [STATE_DIR]

Stop the aiwb GUI server previously started by start.sh.

STATE_DIR defaults to .auxiliary/temporary/state/web-smoke-test.
EOF
  exit 0
fi

STATE_DIR="${1:-.auxiliary/temporary/state/web-smoke-test}"
STATE_DIR="$(cd "$STATE_DIR" && pwd 2>/dev/null || echo "$STATE_DIR")"
PID_FILE="$STATE_DIR/.aiwb-gui-pids"

if [ ! -f "$PID_FILE" ]; then
  echo "==> No PID file found — nothing to stop"
  echo "    (If aiwb is running from a manual start, kill it directly.)"
  exit 0
fi

echo "==> Reading PID file: $PID_FILE"
STOPPED=0
while IFS= read -r line; do
  name="${line%%:*}"
  pid="${line#*:}"
  # Try the recorded PID first, then fall back to the process group (setsid
  # in start.sh detaches via a new session). Finally fall back to pkill by
  # command name in case the recorded PID was a transient shell wrapper.
  if kill -0 "$pid" 2>/dev/null; then
    kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
    echo "    stopped $name (pid=$pid)" && STOPPED=1
  elif kill -0 "-$pid" 2>/dev/null; then
    kill -- "-$pid" 2>/dev/null
    echo "    stopped $name (pgid=$pid)" && STOPPED=1
  else
    echo "    $name (pid=$pid) already dead"
  fi
done < "$PID_FILE"
# Belt-and-suspenders: kill any leftover aiwb python processes bound to the
# recorded PID's command line.
pkill -f 'aiwb --gui-address' 2>/dev/null && STOPPED=1 || true
rm -f "$PID_FILE"

# Wait for port to be released (up to 10s)
for i in $(seq 1 10); do
  if ! lsof -ti:5006 >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if [ "$STOPPED" -eq 0 ]; then
  echo "==> All recorded processes already dead"
fi

echo ""
echo "=== Done ==="
