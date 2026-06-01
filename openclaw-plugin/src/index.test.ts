import { describe, expect, it } from "vitest";
import entry from "./index.js";
import { getToolPluginMetadata } from "openclaw/plugin-sdk/tool-plugin";

describe("openclaw-mcp-printer", () => {
  it("declares tool metadata", () => {
    expect(getToolPluginMetadata(entry)?.tools.map((tool) => tool.name)).toEqual([
      "printer_list",
      "printer_status",
      "printer_upload_gcode",
      "printer_start_print",
      "printer_pause",
      "printer_resume",
      "printer_cancel",
      "printer_emergency_stop",
    ]);
  });

  it("marks emergency stop as optional", () => {
    const emergencyStop = getToolPluginMetadata(entry)?.tools.find((tool) => tool.name === "printer_emergency_stop");

    expect(emergencyStop?.optional).toBe(true);
  });
});
