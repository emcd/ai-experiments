#!/usr/bin/env bash
# Starts the AI Workbench (aiwb) GUI server for local development and
# Playwright smoke testing. Patterned after litrpg/scripts/web-dev/start.sh.
#
# Usage: scripts/web-dev/start.sh [STATE_DIR]
#
# STATE_DIR defaults to .auxiliary/temporary/state/web-smoke-test and holds
# the PID file plus any server logs.
#
# Cleanup ownership: this harness kills only its own process group via
# `kill -- -<pid>` against the recorded setsid session leader PID. It
# never runs unscoped pattern-matching kills (no pkill -f), so an
# unrelated manually-launched aiwb on a different port is left alone.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  cat <<EOF
Usage: $0 [STATE_DIR]

Start the aiwb GUI server (Hatch-launched Panel/Bokeh) for local
development and Playwright smoke testing.

STATE_DIR defaults to .auxiliary/temporary/state/web-smoke-test.
EOF
  exit 0
fi

STATE_DIR="${1:-.auxiliary/temporary/state/web-smoke-test}"
mkdir -p "$STATE_DIR"
STATE_DIR="$(cd "$STATE_DIR" && pwd)"
PID_FILE="$STATE_DIR/.aiwb-gui-pids"
GUI_PORT=5006
GUI_ADDRESS="127.0.0.1"

# --- Kill previous harness-owned run if PID file exists ---
# Tear down the recorded process group (setsid session leader). This
# is scoped strictly to PIDs we previously recorded; nothing else.
if [ -f "$PID_FILE" ]; then
  echo "==> Cleaning up previous run..."
  while IFS= read -r line; do
    name="${line%%:*}"
    pid="${line#*:}"
    if kill -0 "$pid" 2>/dev/null; then
      # Prefer the process group kill so any hatch/python children are
      # taken down too; fall back to the recorded PID if the group has
      # already been reaped.
      kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
      echo "    stopped $name (pgid=$pid)"
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
  for i in $(seq 1 10); do
    if ! lsof -ti:"$GUI_PORT" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

# --- Fail fast if port is already in use ---
if lsof -ti:"$GUI_PORT" >/dev/null 2>&1; then
  echo "==> ERROR: port $GUI_PORT already in use (expected for aiwb GUI)" >&2
  echo "    Kill the existing process first or use a different state directory." >&2
  exit 1
fi

# --- Start aiwb GUI under setsid ---
# setsid creates a new session and process group; the leader PID is
# what $! captures and what we record. Killing that process group via
# `kill -- -<pid>` (in stop.sh) takes down the full hatch/python tree.
echo "==> Starting aiwb GUI (state=$STATE_DIR, port=$GUI_PORT)..."
LOG_FILE="$STATE_DIR/aiwb-gui.log"
setsid bash -c "exec hatch run aiwb -- \
  --gui-address '$GUI_ADDRESS' \
  --gui-port '$GUI_PORT' \
  --no-open-browser \
  >'$LOG_FILE' 2>&1" </dev/null &
AIWB_PID=$!
echo "aiwb:$AIWB_PID" > "$PID_FILE"

echo "==> Waiting for GUI server on $GUI_ADDRESS:$GUI_PORT..."
GUI_READY=false
for i in $(seq 1 30); do
  # Liveness check via the process group (negative PID). This survives
  # the hatch/aiwb exec-replace dance without needing to discover the
  # current leading process by name.
  if ! kill -0 "-$AIWB_PID" 2>/dev/null && ! kill -0 "$AIWB_PID" 2>/dev/null; then
    echo "==> ERROR: aiwb process (pgid=$AIWB_PID) died during startup" >&2
    echo "    Last 20 lines of log:" >&2
    tail -20 "$LOG_FILE" 2>/dev/null | sed 's/^/    /' >&2 || true
    rm -f "$PID_FILE"
    exit 1
  fi
  if curl -sf -o /dev/null "http://$GUI_ADDRESS:$GUI_PORT/" 2>/dev/null; then
    echo "==> GUI server ready (pgid=$AIWB_PID)"
    GUI_READY=true
    break
  fi
  sleep 1
done

if [ "$GUI_READY" = false ]; then
  echo "==> ERROR: GUI server not ready after 30s" >&2
  echo "    Last 20 lines of log:" >&2
  tail -20 "$LOG_FILE" 2>/dev/null | sed 's/^/    /' >&2 || true
  kill -- "-$AIWB_PID" 2>/dev/null || kill "$AIWB_PID" 2>/dev/null || true
  rm -f "$PID_FILE"
  exit 1
fi

echo ""
echo "=== aiwb GUI running ==="
echo "  PGID:     $AIWB_PID (session leader)"
echo "  URL:      http://$GUI_ADDRESS:$GUI_PORT/"
echo "  State:    $STATE_DIR"
echo "  Log:      $LOG_FILE"
echo ""
echo "  Stop: $(dirname "$0")/stop.sh"
