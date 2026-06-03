#!/usr/bin/env bash
set -euo pipefail

ORIGINAL_CWD="$(pwd)"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_PATH="$ROOT_DIR/printers.json"
MODE="auto"
FORCE=0
RESTART_GATEWAY=0
OPENCLAW_BIN="${OPENCLAW_BIN:-}"
OPENCLAW_PROFILE=""
OPENCLAW_DEV=0
OPENCLAW_TIMEOUT_MS="${OPENCLAW_TIMEOUT_MS:-10000}"
OPENCLAW_CMD=()
WORK_DIR=""
REGISTER_CHANGED=0

usage() {
  cat <<'EOF'
Usage: scripts/install_openclaw_e2e.sh [options]

Install MCP Printer locally, smoke test the MCP stdio server, detect OpenClaw,
and safely register MCP Printer with a running OpenClaw/Clawbot setup.

Options:
  --mode auto|server|plugin   Registration path. Default: auto.
                              auto prefers the standard MCP server, then plugin.
  --config PATH               Printer config path. Default: ./printers.json.
  --force                     Replace a conflicting existing registration.
  --restart-gateway           Run openclaw gateway restart --safe after changes.
  --openclaw-bin PATH         OpenClaw CLI path. Default: first openclaw in PATH.
  --openclaw-profile NAME     Pass --profile NAME to OpenClaw.
  --openclaw-dev              Pass --dev to OpenClaw.
  -h, --help                  Show this help.

Environment:
  OPENCLAW_BIN                Alternate OpenClaw CLI path.
  OPENCLAW_TIMEOUT_MS         OpenClaw probe timeout in milliseconds.
EOF
}

log() {
  printf '\n==> %s\n' "$*"
}

warn() {
  printf 'WARN: %s\n' "$*" >&2
}

die() {
  local message="$1"
  local code="${2:-1}"
  printf 'ERROR: %s\n' "$message" >&2
  exit "$code"
}

cleanup() {
  if [[ -n "$WORK_DIR" && -d "$WORK_DIR" ]]; then
    rm -rf "$WORK_DIR"
  fi
}

trap cleanup EXIT

abs_path() {
  local input="$1"
  local path
  if [[ "$input" = /* ]]; then
    path="$input"
  else
    path="$ORIGINAL_CWD/$input"
  fi

  local dir
  local base
  dir="$(dirname "$path")"
  base="$(basename "$path")"

  if [[ -d "$dir" ]]; then
    (cd "$dir" && printf '%s/%s\n' "$PWD" "$base")
  else
    printf '%s\n' "$path"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      [[ $# -ge 2 ]] || die "--mode requires auto, server, or plugin."
      MODE="$2"
      shift 2
      ;;
    --config)
      [[ $# -ge 2 ]] || die "--config requires a path."
      CONFIG_PATH="$(abs_path "$2")"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --restart-gateway)
      RESTART_GATEWAY=1
      shift
      ;;
    --openclaw-bin)
      [[ $# -ge 2 ]] || die "--openclaw-bin requires a path."
      OPENCLAW_BIN="$2"
      shift 2
      ;;
    --openclaw-profile)
      [[ $# -ge 2 ]] || die "--openclaw-profile requires a profile name."
      OPENCLAW_PROFILE="$2"
      shift 2
      ;;
    --openclaw-dev)
      OPENCLAW_DEV=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
done

case "$MODE" in
  auto|server|plugin)
    ;;
  *)
    die "--mode must be auto, server, or plugin."
    ;;
esac

WORK_DIR="$(mktemp -d)"

python_bin() {
  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    printf '%s\n' "$ROOT_DIR/.venv/bin/python"
  else
    printf '%s\n' "python3"
  fi
}

detect_openclaw() {
  local bin="$OPENCLAW_BIN"
  if [[ -z "$bin" ]]; then
    bin="$(command -v openclaw || true)"
  fi

  [[ -n "$bin" ]] || die "OpenClaw CLI was not found in PATH. Install or start OpenClaw, then rerun this script." 2
  [[ -x "$bin" || "$bin" == "openclaw" ]] || die "OpenClaw CLI is not executable: $bin" 2

  OPENCLAW_CMD=("$bin")
  if [[ "$OPENCLAW_DEV" == "1" ]]; then
    OPENCLAW_CMD+=("--dev")
  fi
  if [[ -n "$OPENCLAW_PROFILE" ]]; then
    OPENCLAW_CMD+=("--profile" "$OPENCLAW_PROFILE")
  fi
}

oc() {
  "${OPENCLAW_CMD[@]}" "$@"
}

supports_openclaw_command() {
  oc "$@" --help >/dev/null 2>&1
}

json_files_equal() {
  "$(python_bin)" - "$1" "$2" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as left_file:
    left = json.load(left_file)
with open(sys.argv[2], encoding="utf-8") as right_file:
    right = json.load(right_file)

sys.exit(0 if left == right else 1)
PY
}

json_has_empty_printers() {
  "$(python_bin)" - "$1" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    value = json.load(handle)

sys.exit(0 if isinstance(value, dict) and value.get("printers") == [] else 1)
PY
}

ensure_openclaw_running() {
  local status_json="$WORK_DIR/openclaw-gateway-status.json"
  local status_err="$WORK_DIR/openclaw-gateway-status.err"
  local health_json="$WORK_DIR/openclaw-health.json"
  local health_err="$WORK_DIR/openclaw-health.err"

  if oc gateway status --json --require-rpc --timeout "$OPENCLAW_TIMEOUT_MS" >"$status_json" 2>"$status_err"; then
    return 0
  fi

  if oc health --json --timeout "$OPENCLAW_TIMEOUT_MS" >"$health_json" 2>"$health_err"; then
    return 0
  fi

  if [[ -s "$status_err" ]]; then
    sed 's/^/  /' "$status_err" >&2
  fi
  if [[ -s "$health_err" ]]; then
    sed 's/^/  /' "$health_err" >&2
  fi
  return 1
}

select_mode() {
  case "$MODE" in
    server)
      supports_openclaw_command mcp set && supports_openclaw_command mcp show \
        || die "This OpenClaw CLI does not support 'openclaw mcp set/show'." 2
      printf '%s\n' "server"
      ;;
    plugin)
      supports_openclaw_command plugins install && supports_openclaw_command plugins inspect \
        || die "This OpenClaw CLI does not support 'openclaw plugins install/inspect'." 2
      printf '%s\n' "plugin"
      ;;
    auto)
      if supports_openclaw_command mcp set && supports_openclaw_command mcp show; then
        printf '%s\n' "server"
      elif supports_openclaw_command plugins install && supports_openclaw_command plugins inspect; then
        printf '%s\n' "plugin"
      else
        die "OpenClaw was detected, but neither MCP registration nor plugin install commands are available." 2
      fi
      ;;
  esac
}

register_server() {
  local server_json="$WORK_DIR/mcp-printer.server.json"
  local existing_json="$WORK_DIR/existing-mcp-printer.server.json"
  local actual_json="$WORK_DIR/actual-mcp-printer.server.json"

  log "Generating MCP server definition"
  "$ROOT_DIR/.venv/bin/mcp-printer" --print-clawbot-config --config "$CONFIG_PATH" >"$server_json"

  if [[ "$CONFIG_PATH" == "$ROOT_DIR/printers.json" ]]; then
    cp "$server_json" "$ROOT_DIR/clawbot-mcp-printer.server.json"
  fi

  if oc mcp show mcp-printer --json >"$existing_json" 2>/dev/null; then
    if json_files_equal "$existing_json" "$server_json"; then
      log "OpenClaw already has the matching mcp-printer server registration"
    elif [[ "$FORCE" == "1" ]]; then
      log "Replacing existing OpenClaw mcp-printer server registration"
      oc mcp set mcp-printer "$(<"$server_json")"
      REGISTER_CHANGED=1
    else
      die "OpenClaw already has an mcp-printer MCP server with different settings. Rerun with --force to replace it, or inspect it with 'openclaw mcp show mcp-printer --json'." 3
    fi
  else
    log "Registering mcp-printer with OpenClaw MCP config"
    oc mcp set mcp-printer "$(<"$server_json")"
    REGISTER_CHANGED=1
  fi

  oc mcp show mcp-printer --json >"$actual_json"
  json_files_equal "$actual_json" "$server_json" \
    || die "OpenClaw MCP registration did not match the generated server definition." 1

  log "OpenClaw MCP server registration verified"
}

build_plugin_config() {
  "$(python_bin)" - "$CONFIG_PATH" <<'PY'
import json
import sys

source_path = sys.argv[1]
with open(source_path, encoding="utf-8") as handle:
    raw = json.load(handle)

printers = []
for printer in raw.get("printers", []):
    converted = {
        "id": str(printer["id"]),
        "name": str(printer.get("name") or printer["id"]),
        "type": str(printer["type"]).lower(),
        "baseUrl": str(printer["base_url"]).rstrip("/"),
    }
    if printer.get("api_key_env"):
        converted["apiKeyEnv"] = str(printer["api_key_env"])
    if printer.get("api_key"):
        converted["apiKey"] = str(printer["api_key"])
    if printer.get("camera_id"):
        converted["cameraId"] = str(printer["camera_id"])
    printers.append(converted)

print(json.dumps({"printers": printers}, indent=2))
PY
}

plugin_matches_checkout() {
  "$(python_bin)" - "$1" "$ROOT_DIR/openclaw-plugin" <<'PY'
import json
import os
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

plugin = payload.get("plugin", payload)
expected = os.path.realpath(sys.argv[2])
candidates = [
    plugin.get("rootDir"),
    plugin.get("install", {}).get("installPath"),
    plugin.get("install", {}).get("sourcePath"),
]

for candidate in candidates:
    if candidate and os.path.realpath(candidate) == expected:
        sys.exit(0)

sys.exit(1)
PY
}

verify_plugin_runtime() {
  "$(python_bin)" - "$1" <<'PY'
import json
import sys

required = {
    "printer_list",
    "printer_status",
    "printer_upload_gcode",
    "printer_emergency_stop",
}

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

plugin = payload.get("plugin", {})
if plugin.get("enabled") is not True:
    print("Plugin runtime check failed: plugin is not enabled.", file=sys.stderr)
    sys.exit(1)
if plugin.get("status") not in {"loaded", "active"}:
    print(f"Plugin runtime check failed: status is {plugin.get('status')!r}.", file=sys.stderr)
    sys.exit(1)

tool_names = set(plugin.get("toolNames") or [])
if not tool_names:
    for tool in payload.get("tools") or []:
        for name in tool.get("names") or []:
            tool_names.add(name)

missing = sorted(required - tool_names)
if missing:
    print(f"Plugin runtime check failed: missing expected tools: {', '.join(missing)}.", file=sys.stderr)
    sys.exit(1)
PY
}

register_plugin() {
  local inspect_json="$WORK_DIR/plugin-inspect.json"
  local runtime_json="$WORK_DIR/plugin-runtime.json"
  local plugin_config="$WORK_DIR/openclaw-plugin-config.json"
  local existing_config="$WORK_DIR/existing-openclaw-plugin-config.json"

  command -v npm >/dev/null 2>&1 || die "Plugin mode requires npm, but npm was not found." 2

  log "Building and validating the native OpenClaw plugin"
  (cd "$ROOT_DIR/openclaw-plugin" && npm install && npm run plugin:validate && npm test)

  if oc plugins inspect openclaw-mcp-printer --json >"$inspect_json" 2>/dev/null; then
    if plugin_matches_checkout "$inspect_json"; then
      log "OpenClaw plugin is already installed from this checkout"
    elif [[ "$FORCE" == "1" ]]; then
      log "Replacing existing OpenClaw plugin install"
      oc plugins install "$ROOT_DIR/openclaw-plugin" --link --force
      REGISTER_CHANGED=1
    else
      die "OpenClaw already has an openclaw-mcp-printer plugin from another location. Rerun with --force to replace it." 3
    fi
  else
    log "Installing OpenClaw plugin from this checkout"
    oc plugins install "$ROOT_DIR/openclaw-plugin" --link
    REGISTER_CHANGED=1
  fi

  log "Enabling OpenClaw plugin"
  oc plugins enable openclaw-mcp-printer

  build_plugin_config >"$plugin_config"
  if oc config get plugins.entries.openclaw-mcp-printer.config --json >"$existing_config" 2>/dev/null; then
    if json_files_equal "$existing_config" "$plugin_config"; then
      log "OpenClaw plugin printer config already matches $CONFIG_PATH"
    elif json_has_empty_printers "$existing_config"; then
      log "Writing OpenClaw plugin printer config"
      oc config set plugins.entries.openclaw-mcp-printer.config "$(<"$plugin_config")" --json
      REGISTER_CHANGED=1
    elif [[ "$FORCE" == "1" ]]; then
      log "Replacing existing OpenClaw plugin printer config"
      oc config set plugins.entries.openclaw-mcp-printer.config "$(<"$plugin_config")" --json
      REGISTER_CHANGED=1
    else
      die "OpenClaw plugin config already has printers and differs from $CONFIG_PATH. Rerun with --force to replace it." 3
    fi
  else
    log "Writing OpenClaw plugin printer config"
    oc config set plugins.entries.openclaw-mcp-printer.config "$(<"$plugin_config")" --json
    REGISTER_CHANGED=1
  fi

  oc plugins inspect openclaw-mcp-printer --json --runtime >"$runtime_json"
  verify_plugin_runtime "$runtime_json"
  log "OpenClaw plugin runtime verified"
}

restart_gateway_if_requested() {
  if [[ "$RESTART_GATEWAY" != "1" ]]; then
    if [[ "$REGISTER_CHANGED" == "1" ]]; then
      warn "OpenClaw config changed. Restart the gateway if your setup does not hot-reload config, or rerun this script with --restart-gateway."
    fi
    return 0
  fi

  supports_openclaw_command gateway restart \
    || die "This OpenClaw CLI does not support 'openclaw gateway restart'." 2

  log "Restarting OpenClaw gateway safely"
  oc gateway restart --safe --json >"$WORK_DIR/openclaw-gateway-restart.json"

  log "Verifying OpenClaw gateway after restart"
  ensure_openclaw_running \
    || die "OpenClaw gateway did not become reachable after restart." 2
}

main() {
  cd "$ROOT_DIR"

  local config_dir
  config_dir="$(dirname "$CONFIG_PATH")"
  [[ -d "$config_dir" ]] || die "Config directory does not exist: $config_dir"

  log "Installing MCP Printer locally"
  "$ROOT_DIR/scripts/install_local.sh"

  if [[ ! -f "$CONFIG_PATH" ]]; then
    log "Creating printer config at $CONFIG_PATH"
    "$ROOT_DIR/.venv/bin/mcp-printer" --init-config --config "$CONFIG_PATH"
  fi

  log "Running local MCP smoke test"
  "$ROOT_DIR/scripts/smoke_mcp.sh" "$CONFIG_PATH"

  detect_openclaw
  log "Detected OpenClaw CLI: ${OPENCLAW_CMD[*]}"
  oc --version

  log "Checking for a running OpenClaw gateway"
  ensure_openclaw_running \
    || die "OpenClaw CLI was found, but the gateway is not reachable. Start OpenClaw/Clawbot, then rerun this script." 2

  local selected_mode
  selected_mode="$(select_mode)"
  log "Using OpenClaw registration mode: $selected_mode"

  if [[ "$selected_mode" == "server" ]]; then
    register_server
  else
    register_plugin
  fi

  restart_gateway_if_requested

  cat <<EOF

MCP Printer OpenClaw end-to-end check passed.

Mode: $selected_mode
Config: $CONFIG_PATH
OpenClaw: ${OPENCLAW_CMD[*]}

Next safe prompt for Clawbot/OpenClaw:
  List my configured 3D printers.
EOF
}

main "$@"
