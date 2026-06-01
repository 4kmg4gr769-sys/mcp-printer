#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_PATH="${1:-"$ROOT_DIR/printers.json"}"
SERVER_BIN="${ROOT_DIR}/.venv/bin/mcp-printer"
SERVER_ARGS=()

if [[ ! -x "$SERVER_BIN" ]]; then
  SERVER_BIN="python3"
  SERVER_ARGS=(-m mcp_printer)
fi

printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | "$SERVER_BIN" "${SERVER_ARGS[@]+"${SERVER_ARGS[@]}"}" --config "$CONFIG_PATH"
