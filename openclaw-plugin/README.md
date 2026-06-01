# MCP Printer

OpenClaw plugin for sending jobs to OctoPrint and Moonraker/Klipper 3D printers.

Built by Steve Villari and Villocity Labs.

## Tools

- `printer_list`
- `printer_status`
- `printer_upload_gcode`
- `printer_start_print`
- `printer_pause`
- `printer_resume`
- `printer_cancel`
- `printer_emergency_stop`

## Configuration

Configure printers under `plugins.entries.openclaw-mcp-printer.config`:

```json
{
  "plugins": {
    "entries": {
      "openclaw-mcp-printer": {
        "enabled": true,
        "config": {
          "printers": [
            {
              "id": "workbench",
              "name": "Workbench Printer",
              "type": "octoprint",
              "baseUrl": "http://octopi.local",
              "apiKeyEnv": "OCTOPRINT_API_KEY",
              "cameraId": "printer-cam"
            },
            {
              "id": "voron",
              "name": "Voron",
              "type": "moonraker",
              "baseUrl": "http://voron.local",
              "apiKeyEnv": "MOONRAKER_API_KEY",
              "cameraId": "voron-cam"
            }
          ]
        }
      }
    },
    "load": {
      "paths": ["./openclaw-plugin"]
    }
  }
}
```

Keep API keys in environment variables or OpenClaw secrets when possible.

## Local Install

```bash
openclaw plugins install ./openclaw-plugin --link
openclaw plugins inspect openclaw-mcp-printer --runtime
```

Restart the OpenClaw gateway after installing or changing config.

## Build

```bash
npm install
npm run plugin:build
npm run plugin:validate
npm test
```
