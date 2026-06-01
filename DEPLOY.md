# Deploying MCP Printer To Clawbot / OpenClaw

This guide assumes you have Clawbot/OpenClaw installed and want it to launch MCP Printer as a local stdio MCP server.

MCP Printer was built by Steve Villari and Villocity Labs.

## 1. Prepare This Project

From this folder:

```bash
cd "/Users/SteveVillari/Documents/MCP Printer"
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests
```

## 2. Create Your Printer Config

Generate a local config:

```bash
.venv/bin/mcp-printer --init-config --config ./printers.json
```

Edit `printers.json` with your printer details. Keep `api_key_env` in the file instead of hardcoding API keys:

```json
{
  "printers": [
    {
      "id": "workbench",
      "name": "Workbench Printer",
      "type": "octoprint",
      "base_url": "http://octopi.local",
      "api_key_env": "OCTOPRINT_API_KEY"
    }
  ]
}
```

Supported `type` values:

- `octoprint`
- `moonraker`

## 3. Test The MCP Server Locally

Run:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | OCTOPRINT_API_KEY="your-key" .venv/bin/mcp-printer --config ./printers.json
```

You should see JSON responses with `serverInfo.name` set to `mcp-printer` and tools like `printer_list`, `printer_status`, and `printer_upload_gcode`.

## 4. Add It To Clawbot / OpenClaw

Generate the exact server JSON:

```bash
.venv/bin/mcp-printer --print-clawbot-config --config ./printers.json
```

If your OpenClaw CLI supports MCP registry commands, run this from the same folder:

```bash
openclaw mcp set mcp-printer "$(.venv/bin/mcp-printer --print-clawbot-config --config ./printers.json)"
```

If you configure MCP servers through a JSON file instead, add this under `mcp.servers`:

```json
{
  "command": "/Users/SteveVillari/Documents/MCP Printer/.venv/bin/mcp-printer",
  "args": [
    "--config",
    "/Users/SteveVillari/Documents/MCP Printer/printers.json"
  ],
  "env": {
    "OCTOPRINT_API_KEY": "your-octoprint-key",
    "MOONRAKER_API_KEY": "your-moonraker-key"
  },
  "cwd": "/Users/SteveVillari/Documents/MCP Printer"
}
```

In a full config file, it usually looks like:

```json
{
  "mcp": {
    "servers": {
      "mcp-printer": {
        "command": "/Users/SteveVillari/Documents/MCP Printer/.venv/bin/mcp-printer",
        "args": [
          "--config",
          "/Users/SteveVillari/Documents/MCP Printer/printers.json"
        ],
        "env": {
          "OCTOPRINT_API_KEY": "your-octoprint-key",
          "MOONRAKER_API_KEY": "your-moonraker-key"
        },
        "cwd": "/Users/SteveVillari/Documents/MCP Printer"
      }
    }
  }
}
```

Restart Clawbot/OpenClaw after adding the server.

## 5. First Safe Test In Clawbot

Ask Clawbot:

```text
List my configured 3D printers.
```

Then:

```text
Get the status of printer workbench.
```

Only upload or start a print after you have confirmed the printer status looks right.

## Troubleshooting

- If Clawbot says the server is missing, verify the absolute `command` path exists.
- If printer calls fail with `401` or `403`, check the API key environment variable in the MCP server config.
- If uploads fail, confirm the file ends in `.gcode`, `.gco`, or `.gc`.
- If the printer is not reachable, open the configured `base_url` in a browser from the same machine.
