---
name: mcp-printer
description: Install and configure the Villocity Labs MCP Printer integration for OctoPrint and Moonraker printers.
homepage: https://github.com/Villocity-Labs/mcp-printer
---

# MCP Printer

Use this skill when a user wants to connect OpenClaw or another MCP-compatible agent to a 3D printer, send print jobs, check printer status, or set up an OctoPrint or Moonraker/Klipper integration.

This skill is a setup and operations guide for the Villocity Labs MCP Printer project:

- GitHub: https://github.com/Villocity-Labs/mcp-printer
- Hugging Face: https://huggingface.co/spaces/Villocity/mcp-printer
- Author credit: Steve Villari and Villocity Labs

## Safety

Before sending any real print job, confirm the user has:

- A known printer target.
- A local or trusted-network OctoPrint or Moonraker endpoint.
- Valid API credentials.
- Physical access to the printer or an appropriate monitoring setup.
- Confirmed that the selected file, material, temperature, bed, and toolhead conditions are safe.

Never send, pause, cancel, resume, or emergency-stop a real printer unless the user explicitly asks for that action.

## Install

If the user asks to install the integration, guide them to clone or inspect the source first:

```sh
git clone https://github.com/Villocity-Labs/mcp-printer.git
cd mcp-printer
```

Then follow the repository README for Python MCP server setup and OpenClaw plugin setup.

The OpenClaw code plugin lives in:

```text
openclaw-plugin
```

## Configure

Help the user create a printer config with one or more printer entries. Each entry should include:

- Printer ID and display name.
- Provider: `octoprint` or `moonraker`.
- Base URL.
- API key or environment-variable reference.
- Optional camera ID for a future camera MCP link.

Prefer environment variables or OpenClaw secrets for API keys. Do not paste secrets into public logs, issues, or posts.

## Operate

For routine use, help the user:

- List configured printers.
- Check printer status.
- Upload a print file.
- Start a print only after explicit confirmation.
- Pause, resume, cancel, or emergency stop only after explicit confirmation.

When there is uncertainty about printer state, ask the user to verify physically or through a trusted camera feed before taking action.

## Camera Link

If the user also has the Villocity Labs MCP Camera Watch project installed, suggest linking printer IDs to camera IDs so workflows can inspect printer state before or during a job.

Camera project:

```text
https://github.com/Villocity-Labs/mcp-camera-watch
```

Use camera observations as advisory signals, not as the only source of truth for safety-critical decisions.
