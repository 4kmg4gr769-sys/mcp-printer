# MCP Printer

A lightweight MCP server for sending 3D print jobs from Clawbot or any MCP-compatible agent to real printers.

Built by Steve Villari and Villocity Labs.

## Features

- Install as an OpenClaw plugin or run as a standard MCP stdio server.
- Register one or more printers in a local JSON config.
- Check printer status.
- Upload `.gcode`, `.gco`, or `.gc` files.
- Start uploaded jobs.
- Pause, resume, cancel, or emergency-stop a print.
- Supports:
  - OctoPrint
- Moonraker / Klipper

## Companion Camera MCP

The planned camera companion should live as a separate project. The integration contract is documented in [CAMERA_MCP_SPEC.md](CAMERA_MCP_SPEC.md), with a printer link example at [examples/printer-camera-link.example.json](examples/printer-camera-link.example.json).

The short version: MCP Printer stays focused on machine control, while the camera MCP evaluates visual conditions such as filament colors, bed readiness, and possible misprints. Agents can orchestrate both, and MCP Printer can later call the camera service through an optional local HTTP bridge.

## Quick Start

```bash
python3 -m mcp_printer --init-config
```

Edit the generated `printers.json` file:

```json
{
  "printers": [
    {
      "id": "workbench",
      "name": "Workbench Printer",
      "type": "octoprint",
      "base_url": "http://octopi.local",
      "api_key_env": "OCTOPRINT_API_KEY",
      "camera_id": "printer-cam"
    },
    {
      "id": "voron",
      "name": "Voron",
      "type": "moonraker",
      "base_url": "http://voron.local",
      "api_key_env": "MOONRAKER_API_KEY"
    }
  ]
}
```

You can also start from [examples/printers.example.json](examples/printers.example.json).

Set any API keys referenced by the config:

```bash
export OCTOPRINT_API_KEY="your-octoprint-key"
export MOONRAKER_API_KEY="your-moonraker-key"
```

Run the MCP server:

```bash
python3 -m mcp_printer --config ./printers.json
```

## Add To Clawbot

For a running OpenClaw/Clawbot setup, the one-command tester path is:

```bash
scripts/install_openclaw_e2e.sh --restart-gateway
```

That command reuses [scripts/install_local.sh](scripts/install_local.sh) and [scripts/smoke_mcp.sh](scripts/smoke_mcp.sh), detects the OpenClaw CLI and running gateway, registers `mcp-printer` when the name is unused or already matches this checkout, and verifies the saved OpenClaw registration. It will stop before replacing a different existing `mcp-printer` entry unless you pass `--force`.

The default mode registers MCP Printer as a standard MCP stdio server. To test the native OpenClaw plugin wrapper instead:

```bash
scripts/install_openclaw_e2e.sh --mode plugin --restart-gateway
```

For a full walkthrough, see [DEPLOY.md](DEPLOY.md).
For community publishing notes, see [PUBLISH.md](PUBLISH.md).

## OpenClaw Plugin

The installable OpenClaw plugin wrapper lives in [openclaw-plugin](openclaw-plugin).

Build and validate it:

```bash
cd openclaw-plugin
npm install
npm run plugin:validate
npm test
```

Install locally while developing:

```bash
openclaw plugins install ./openclaw-plugin --link
openclaw plugins inspect openclaw-mcp-printer --runtime
```

Example plugin config: [examples/openclaw-plugin-config.json](examples/openclaw-plugin-config.json).

Add this server to your Clawbot MCP configuration:

```json
{
  "mcpServers": {
    "mcp-printer": {
      "command": "python3",
      "args": [
        "-m",
        "mcp_printer",
        "--config",
        "/absolute/path/to/printers.json"
      ],
      "env": {
        "OCTOPRINT_API_KEY": "your-octoprint-key",
        "MOONRAKER_API_KEY": "your-moonraker-key"
      }
    }
  }
}
```

An editable example lives at [examples/clawbot.mcp.json](examples/clawbot.mcp.json).

Restart Clawbot after saving the config.

You can generate a local server definition automatically:

```bash
python3 -m mcp_printer --print-clawbot-config --config ./printers.json
```

## Available Tools

- `printer_list`
- `printer_status`
- `printer_upload_gcode`
- `printer_start_print`
- `printer_pause`
- `printer_resume`
- `printer_cancel`
- `printer_emergency_stop`

## Safety Notes

This server can move hot, motorized machines. Keep printers supervised, validate G-code before sending it, and use `printer_emergency_stop` if a job becomes unsafe.

## Development

Run the dependency-free test suite:

```bash
python3 -m unittest discover -s tests
```

## License

MIT. See [LICENSE](LICENSE).
