#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests

if [[ ! -f printers.json ]]; then
  .venv/bin/mcp-printer --init-config --config ./printers.json
fi

.venv/bin/mcp-printer --print-clawbot-config --config ./printers.json > ./clawbot-mcp-printer.server.json

cat <<'EOF'
MCP Printer local setup is ready.

Next files:
- printers.json: edit this with your printer URL and API key env var names.
- clawbot-mcp-printer.server.json: paste this server definition into Clawbot/OpenClaw.

To smoke test:
  scripts/smoke_mcp.sh

To install into a running OpenClaw/Clawbot setup and verify end to end:
  scripts/install_openclaw_e2e.sh --restart-gateway
EOF
