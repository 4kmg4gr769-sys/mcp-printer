# Publishing MCP Printer For OpenClaw

There are two useful release paths.

## Path 1: GitHub Install

This is the fastest community release.

Users clone the repo and register the MCP server:

```bash
git clone https://github.com/VillocityLabs/mcp-printer.git
cd mcp-printer
scripts/install_local.sh
openclaw mcp set mcp-printer "$(cat clawbot-mcp-printer.server.json)"
```

This path works well for early testers because the MCP server runs locally on the user's machine and can reach printers on their LAN.

## Path 2: OpenClaw / ClawHub Install

This is the polished install path.

OpenClaw's public docs describe ClawHub as the registry for OpenClaw skills and plugins. Published plugins can be installed with:

```bash
openclaw plugins install clawhub:<package-name>
```

The publish flow is:

```bash
clawhub package publish <source> --family code-plugin --dry-run
clawhub package publish <source> --family code-plugin
```

For this project, `<source>` should be the OpenClaw plugin package in `openclaw-plugin/` after it is finished and validated.

## OpenClaw Plugin Status

The OpenClaw plugin wrapper now lives in `openclaw-plugin/`. It exposes these tools:

- `printer_list`
- `printer_status`
- `printer_upload_gcode`
- `printer_start_print`
- `printer_pause`
- `printer_resume`
- `printer_cancel`
- `printer_emergency_stop`

It calls OctoPrint and Moonraker directly from TypeScript so OpenClaw users can install a normal plugin package without setting up the Python MCP server first.

Validate before publishing:

```bash
cd openclaw-plugin
npm install
npm run plugin:validate
npm test
npm --cache /private/tmp/mcp-printer-npm-cache pack --dry-run
```

Then publish the code to GitHub and publish to ClawHub with a dry run first.

## Plugin Config Example

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
              "apiKeyEnv": "OCTOPRINT_API_KEY"
            }
          ]
        }
      }
    }
  }
}
```

## Recommended Public Install Copy

Reusable social and community posts live in [ANNOUNCEMENT.md](ANNOUNCEMENT.md).

Early GitHub release:

```text
MCP Printer is a local MCP server for OpenClaw/Clawbot that lets your agent list printers, check status, upload G-code, start prints, pause/resume/cancel, and emergency-stop OctoPrint or Moonraker/Klipper printers.

Install:
git clone https://github.com/VillocityLabs/mcp-printer.git
cd mcp-printer
scripts/install_local.sh
openclaw mcp set mcp-printer "$(cat clawbot-mcp-printer.server.json)"
```

ClawHub release:

```text
Install MCP Printer for OpenClaw:
openclaw plugins install clawhub:villocity-labs/mcp-printer
```

MCP Printer was built by Steve Villari and Villocity Labs.
