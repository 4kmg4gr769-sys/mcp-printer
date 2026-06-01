# Introducing MCP Printer and MCP Camera Watch

I’m opening up early testing for two local-first MCP projects from Steve Villari and Villocity Labs:

- **MCP Printer**: agent tools for OctoPrint and Moonraker/Klipper 3D printers
- **MCP Camera Watch**: a companion camera MCP for descriptions, visual checks, and condition-based alerts

The idea is simple: agents should be able to help with real-world maker workflows, but the sensitive parts should stay local. Printer URLs, API keys, camera streams, and evidence frames belong on the operator’s machine, not in a random hosted control plane.

## MCP Printer

MCP Printer lets OpenClaw/Clawbot-style agents interact with configured 3D printers.

Current capabilities:

- List configured printers
- Check printer status
- Upload G-code
- Start already-uploaded jobs
- Pause, resume, or cancel active prints
- Emergency stop
- OctoPrint support
- Moonraker/Klipper support
- Native OpenClaw plugin wrapper
- Standard Python stdio MCP server

GitHub:

https://github.com/Villocity-Labs/mcp-printer

## MCP Camera Watch

MCP Camera Watch is a separate companion project. It should not be welded into printer control because camera perception is useful beyond 3D printing.

The camera MCP answers questions like:

- What does the camera see?
- Does this condition appear to be true?
- Should this watch alert the operator?

The first scaffold includes tools for:

- Listing configured cameras
- Capturing snapshots
- Describing what is visible
- Evaluating a true/false visual instruction
- Creating watch instructions
- Starting and stopping watches
- Listing alerts

Example printer use cases:

- Check whether the bed is clear before starting a print
- Identify visible filament/dispenser colors
- Watch for spaghetti-like extrusion
- Watch for a print detaching from the bed
- Describe the current printer scene before deciding what to do

GitHub:

https://github.com/Villocity-Labs/mcp-camera-watch

## Why Two Projects?

Printer control and camera perception have different safety boundaries.

MCP Printer should focus on machine control. MCP Camera Watch should focus on visual understanding and alerts. Agents can use both together, and MCP Printer can later integrate with the camera service through a local HTTP bridge.

That split keeps the system easier to test, easier to trust, and more reusable.

## Feedback Wanted

I’m looking for early testers and feedback.

Questions I’d love help with:

1. Did install/config work on your machine?
2. What printer/controller did you test with?
3. Which printer workflows are missing?
4. What actions should require explicit confirmation?
5. What camera checks would be most useful?
6. Would you trust automatic pause/cancel, or should the first version stay alert-and-ask?
7. What should the OpenClaw install experience look like?

Both projects are early. Test carefully, keep printers supervised, and treat all machine-control tools with respect.

Built by Steve Villari and Villocity Labs.
