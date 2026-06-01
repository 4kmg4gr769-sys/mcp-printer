# MCP Printer Announcement

MCP Printer is ready for early testers.

Built by Steve Villari and Villocity Labs, MCP Printer lets OpenClaw/Clawbot-style agents talk to real 3D printers through local tools. It supports OctoPrint and Moonraker/Klipper, and it can list printers, check status, upload G-code, start prints, pause/resume/cancel jobs, and emergency-stop a printer.

This is intentionally local-first: your printer URL and API keys stay on your machine.

## Short Post

I’m looking for early testers for MCP Printer, a local MCP/OpenClaw plugin for 3D printers.

It lets an agent list printers, check status, upload G-code, start prints, pause/resume/cancel jobs, and emergency-stop OctoPrint or Moonraker/Klipper printers.

Built by me and Villocity Labs. If you run OctoPrint or Klipper and want to try it, I’d love feedback on setup, safety, missing workflows, and what printer automations you actually want.

## LinkedIn / Longer Post

I’m opening up early testing for MCP Printer, a local MCP/OpenClaw plugin for 3D printers built by Steve Villari and Villocity Labs.

The goal is simple: let your agent safely interact with your own printers from your own machine.

Current capabilities:

- List configured printers
- Check printer status
- Upload G-code
- Start already-uploaded jobs
- Pause, resume, or cancel active prints
- Emergency stop
- OctoPrint support
- Moonraker/Klipper support

I made this local-first because printer access and API keys should stay under the owner’s control. No hosted service is required.

I’m especially looking for feedback from people with OctoPrint, Klipper, Voron, Prusa, Bambu-adjacent workflows, print farms, makerspaces, and anyone already experimenting with OpenClaw or MCP tools.

Feedback I’m looking for:

- Was install/config confusing?
- What printer APIs or workflows are missing?
- What safety guardrails would make you trust it?
- What should an agent never be allowed to do without confirmation?
- Would camera-based print monitoring be useful as a linked companion MCP?

Comment or message me if you want to try it.

## Discord / Forum Post

Hey everyone, I’m looking for early testers for MCP Printer.

It’s a local MCP/OpenClaw plugin that lets an agent work with OctoPrint and Moonraker/Klipper printers:

- list printers
- check status
- upload G-code
- start a print
- pause/resume/cancel
- emergency stop

It runs locally so your printer URL and API keys stay on your machine.

Built by Steve Villari and Villocity Labs. I’d love feedback on install, safety, missing printer workflows, and whether a linked camera MCP for print monitoring would be useful.

## X / Short Social

Looking for early testers for MCP Printer.

A local MCP/OpenClaw plugin for OctoPrint + Moonraker/Klipper printers:

- status
- upload G-code
- start/pause/resume/cancel
- emergency stop

Built by Steve Villari + Villocity Labs.

Feedback wanted on setup, safety, and workflows.

## GitHub Release Blurb

MCP Printer `0.1.0` is an early local-first MCP/OpenClaw plugin for controlling OctoPrint and Moonraker/Klipper 3D printers.

This release includes:

- Python stdio MCP server
- Native OpenClaw plugin wrapper
- OctoPrint client
- Moonraker/Klipper client
- Config examples
- Local smoke tests
- OpenClaw plugin validation

This is an alpha release. Test on non-critical printers first, keep prints supervised, and treat all machine-control tools with care.

## Feedback Questions

When asking for feedback, point people at these:

1. What printer/controller did you test with?
2. Did install/config work on the first try?
3. Which tool worked best?
4. Which tool failed or felt unsafe?
5. What workflow should be added next?
6. Should start/cancel/emergency-stop require stronger confirmation?
7. Would linked camera monitoring help, and what should it detect?

## Safety Note

MCP Printer controls hot, motorized machines. Test carefully, keep printers supervised, validate G-code before printing, and do not expose local printer control endpoints to untrusted networks.
