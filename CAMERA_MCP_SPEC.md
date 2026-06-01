# Camera MCP Companion Spec

The camera MCP should be a separate project from MCP Printer, but the two should share a stable integration contract.

Working project name: **MCP Camera Watch**.

Built as a companion concept for Steve Villari and Villocity Labs projects.

## Design Review

The idea is effective and worth splitting into its own MCP because camera perception is a different responsibility than printer control.

MCP Printer should answer: "What can I do to this printer?"

MCP Camera Watch should answer: "What do I see, and did a watched condition become true?"

Keeping them separate gives us:

- Cleaner safety boundaries
- Reusable camera monitoring beyond 3D printing
- Independent model/backend choices
- Easier testing with recorded frames
- A simple path for agents to orchestrate both MCPs together

The main design risk is ambiguous natural language. "Tell me if this misprinted" is useful, but the system should convert that into an explicit watch with a camera, region, cadence, threshold, and evidence requirements.

## Core Concepts

### Camera Source

A configured visual input.

Examples:

- USB camera
- RTSP stream
- HTTP snapshot URL
- Local image folder for testing
- Future: phone camera, browser camera, or printer-native camera endpoint

### Region Of Interest

The place to look.

Regions should use normalized coordinates so they work across resolutions:

```json
{
  "x": 0.1,
  "y": 0.2,
  "width": 0.6,
  "height": 0.5
}
```

The camera MCP should also allow named regions:

```json
{
  "name": "toolhead"
}
```

### Watch Instruction

A condition to evaluate repeatedly.

Example:

```json
{
  "id": "watch-spaghetti",
  "camera_id": "printer-cam",
  "instruction": "Alert if the print appears to have detached from the bed or has spaghetti-like extrusion.",
  "roi": {
    "name": "print-bed"
  },
  "cadence_seconds": 30,
  "confidence_threshold": 0.8,
  "cooldown_seconds": 300
}
```

### Watch Result

A binary outcome with supporting evidence.

```json
{
  "watch_id": "watch-spaghetti",
  "camera_id": "printer-cam",
  "met": true,
  "confidence": 0.87,
  "summary": "Loose filament is visible above the print bed and the part appears detached.",
  "evidence_frame_path": "/path/to/frame.jpg",
  "observed_at": "2026-06-01T13:30:00Z"
}
```

The `met` field is the most important integration point. Agents and other MCPs can treat each instruction as true or false.

## Required MCP Tools

### `camera_list`

List configured camera sources.

Input:

```json
{}
```

Output:

```json
[
  {
    "id": "printer-cam",
    "name": "Printer Camera",
    "type": "snapshot_url"
  }
]
```

### `camera_snapshot`

Capture or fetch one frame.

Input:

```json
{
  "camera_id": "printer-cam",
  "roi": {
    "name": "print-bed"
  }
}
```

Output:

```json
{
  "camera_id": "printer-cam",
  "frame_path": "/path/to/frame.jpg",
  "captured_at": "2026-06-01T13:30:00Z"
}
```

### `camera_evaluate_once`

Evaluate one instruction against the current frame.

Input:

```json
{
  "camera_id": "printer-cam",
  "instruction": "Are the filament dispenser colors red, white, and blue?",
  "roi": {
    "name": "filament-dispenser"
  },
  "confidence_threshold": 0.75
}
```

Output:

```json
{
  "met": true,
  "confidence": 0.82,
  "summary": "The visible dispenser colors appear to be red, white, and blue.",
  "evidence_frame_path": "/path/to/frame.jpg"
}
```

### `camera_describe`

Describe what is visible in the current frame. This is intentionally separate from `camera_evaluate_once`: use description for open-ended observation, and evaluation for true/false conditions.

Input:

```json
{
  "camera_id": "printer-cam",
  "prompt": "Describe the print bed and any visible filament issues.",
  "detail": "normal",
  "roi": {
    "name": "print-bed"
  }
}
```

Output:

```json
{
  "description": "The print bed is visible with a partially completed object near the center. No obvious loose filament is visible.",
  "prompt": "Describe the print bed and any visible filament issues.",
  "detail": "normal",
  "evidence_frame_path": "/path/to/frame.jpg",
  "observed_at": "2026-06-01T13:30:00Z"
}
```

### `camera_watch_create`

Create a persistent watch.

Input:

```json
{
  "camera_id": "printer-cam",
  "instruction": "Alert if the print appears to have misprinted.",
  "roi": {
    "name": "print-bed"
  },
  "cadence_seconds": 30,
  "confidence_threshold": 0.8,
  "cooldown_seconds": 300
}
```

Output:

```json
{
  "watch_id": "watch-01",
  "status": "created"
}
```

### `camera_watch_start`

Start a watch.

Input:

```json
{
  "watch_id": "watch-01"
}
```

Output:

```json
{
  "watch_id": "watch-01",
  "status": "running"
}
```

### `camera_watch_stop`

Stop a watch.

Input:

```json
{
  "watch_id": "watch-01"
}
```

Output:

```json
{
  "watch_id": "watch-01",
  "status": "stopped"
}
```

### `camera_watch_status`

Get watch state and latest result.

Input:

```json
{
  "watch_id": "watch-01"
}
```

Output:

```json
{
  "watch_id": "watch-01",
  "status": "running",
  "latest_result": {
    "met": false,
    "confidence": 0.34,
    "summary": "No visible print failure."
  }
}
```

### `camera_alerts_list`

List recent true-condition alerts.

Input:

```json
{
  "since": "2026-06-01T13:00:00Z"
}
```

Output:

```json
[
  {
    "watch_id": "watch-01",
    "met": true,
    "confidence": 0.87,
    "summary": "The print appears detached.",
    "evidence_frame_path": "/path/to/frame.jpg",
    "observed_at": "2026-06-01T13:30:00Z"
  }
]
```

## Optional HTTP Bridge

Pure MCP is tool-call oriented. For proactive alerts, the camera project should also expose an optional local HTTP bridge:

- `GET /health`
- `POST /evaluate`
- `POST /watches`
- `POST /watches/:id/start`
- `POST /watches/:id/stop`
- `GET /watches/:id`
- `GET /alerts`
- Optional: `GET /events` as Server-Sent Events

This gives MCP Printer a stable service endpoint to call later without needing to become an MCP host itself.

## Printer MCP Integration Contract

MCP Printer should not depend on camera monitoring by default.

Instead, it should optionally accept a camera service configuration:

```json
{
  "camera_service": {
    "base_url": "http://127.0.0.1:8765",
    "printer_camera_map": {
      "workbench": "printer-cam"
    }
  }
}
```

When the camera service exists, MCP Printer can later add optional tools:

- `printer_camera_evaluate`
- `printer_start_monitoring`
- `printer_stop_monitoring`
- `printer_monitoring_status`

For the first linked workflow, keep orchestration at the agent level:

1. Agent calls `printer_status`.
2. Agent calls `camera_evaluate_once` for "bed clear" or "correct filament loaded."
3. Agent calls `printer_start_print` only if camera checks pass.
4. Agent calls `camera_watch_create` for "misprint / detachment / spaghetti."
5. Agent calls `camera_alerts_list` during or after the job.
6. Agent calls `printer_pause` or asks the user before taking action.

## Initial Detection Use Cases

Start with bounded, practical checks:

- Is the print bed clear?
- Is a print visibly detached?
- Is there spaghetti-like extrusion?
- Are the expected filament colors visible?
- Is the nozzle area visibly covered in filament?
- Is the chamber light on?
- Is the printer door open?

Avoid high-confidence claims at first:

- Exact dimensional accuracy
- Hidden layer adhesion defects
- Material identity from color alone
- "This print will succeed" predictions

## Implementation Recommendation

Start with a local Python MCP server because camera tooling is stronger in Python.

Suggested stack:

- Python 3.11+
- Standard MCP stdio server
- `opencv-python` for capture and ROI cropping
- Pluggable evaluator interface
- First evaluator: OpenAI-compatible vision model or local VLM adapter
- Optional second evaluator: lightweight OpenCV color / motion checks
- SQLite or JSONL for watch state and alert history
- Optional FastAPI HTTP bridge for service integration

## MVP Milestones

### Milestone 1: Frame Capture

- Load cameras from config
- Capture snapshots
- Save evidence frames
- Return frame metadata

### Milestone 2: Evaluate Once

- Accept a natural language instruction
- Crop ROI if provided
- Send frame and instruction to evaluator
- Return `met`, `confidence`, `summary`, and evidence path

### Milestone 3: Watches

- Create/start/stop/status tools
- Poll at configured cadence
- Store latest results and true-condition alerts

### Milestone 4: Printer Link

- Add optional HTTP bridge
- Add example workflow connecting MCP Printer and MCP Camera Watch
- Add printer-specific recipes:
  - bed clear before start
  - filament colors match expected materials
  - misprint/spaghetti watch during print

## Acceptance Criteria

The first public alpha is ready when:

- A user can configure an HTTP snapshot camera.
- `camera_snapshot` returns a saved frame path.
- `camera_evaluate_once` returns a clear true/false answer.
- A watch can run for at least 30 minutes without leaking resources.
- Alerts include evidence frames.
- The plugin can run locally without hosting a cloud service.
- MCP Printer can reference the camera service in docs and examples.

## Safety Guidance

Camera monitoring should assist, not replace supervision.

The printer integration should default to "alert and ask" instead of automatically pausing, canceling, or emergency-stopping. Automatic intervention can be added later behind explicit user configuration.
