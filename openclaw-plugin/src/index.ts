import { Type } from "typebox";
import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";
import { readFile } from "node:fs/promises";
import { basename, extname } from "node:path";

const allowedGcodeSuffixes = new Set([".gcode", ".gco", ".gc"]);

const printerSchema = Type.Object({
  id: Type.String({ description: "Stable printer id, for example workbench." }),
  name: Type.Optional(Type.String({ description: "Human-readable printer name." })),
  type: Type.Union([Type.Literal("octoprint"), Type.Literal("moonraker")], {
    description: "Printer API type.",
  }),
  baseUrl: Type.String({ description: "Printer API base URL, for example http://octopi.local." }),
  apiKeyEnv: Type.Optional(Type.String({ description: "Environment variable containing the printer API key." })),
  apiKey: Type.Optional(Type.String({ description: "Printer API key. Prefer apiKeyEnv for shared configs." })),
  cameraId: Type.Optional(Type.String({ description: "Optional camera id from MCP Camera Watch." })),
});

const configSchema = Type.Object(
  {
    printers: Type.Array(printerSchema, {
      description: "3D printers this plugin can control.",
      default: [],
    }),
  },
  { additionalProperties: false },
);

const printerIdParams = Type.Object({
  printerId: Type.String({ description: "Configured printer id." }),
});

export default defineToolPlugin({
  id: "openclaw-mcp-printer",
  name: "MCP Printer",
  description: "Send jobs to OctoPrint and Moonraker 3D printers.",
  configSchema,
  tools: (tool) => [
    tool({
      name: "printer_list",
      label: "List Printers",
      description: "List configured 3D printers.",
      parameters: Type.Object({}),
      execute: (_params, config) =>
        config.printers.map((printer) => ({
          id: printer.id,
          name: printer.name ?? printer.id,
          type: printer.type,
          baseUrl: normalizeBaseUrl(printer.baseUrl),
          ...(printer.cameraId ? { cameraId: printer.cameraId } : {}),
        })),
    }),
    tool({
      name: "printer_status",
      label: "Printer Status",
      description: "Get the current status of a configured 3D printer.",
      parameters: printerIdParams,
      execute: async ({ printerId }, config, context) => clientFor(config, printerId).status(context.signal),
    }),
    tool({
      name: "printer_upload_gcode",
      label: "Upload G-code",
      description: "Upload a local G-code file to a printer, optionally starting the print.",
      parameters: Type.Object({
        printerId: Type.String({ description: "Configured printer id." }),
        filePath: Type.String({ description: "Absolute path to a .gcode, .gco, or .gc file." }),
        start: Type.Optional(Type.Boolean({ description: "Start printing after upload.", default: false })),
      }),
      execute: async ({ printerId, filePath, start }, config, context) =>
        clientFor(config, printerId).uploadGcode(filePath, start ?? false, context.signal),
    }),
    tool({
      name: "printer_start_print",
      label: "Start Print",
      description: "Start printing an already-uploaded file.",
      parameters: Type.Object({
        printerId: Type.String({ description: "Configured printer id." }),
        filename: Type.String({ description: "Uploaded file name or path on the printer." }),
      }),
      execute: async ({ printerId, filename }, config, context) =>
        clientFor(config, printerId).startPrint(filename, context.signal),
    }),
    tool({
      name: "printer_pause",
      label: "Pause Print",
      description: "Pause the active print.",
      parameters: printerIdParams,
      execute: async ({ printerId }, config, context) => clientFor(config, printerId).pause(context.signal),
    }),
    tool({
      name: "printer_resume",
      label: "Resume Print",
      description: "Resume a paused print.",
      parameters: printerIdParams,
      execute: async ({ printerId }, config, context) => clientFor(config, printerId).resume(context.signal),
    }),
    tool({
      name: "printer_cancel",
      label: "Cancel Print",
      description: "Cancel the active print.",
      parameters: printerIdParams,
      execute: async ({ printerId }, config, context) => clientFor(config, printerId).cancel(context.signal),
    }),
    tool({
      name: "printer_emergency_stop",
      label: "Emergency Stop",
      description: "Immediately emergency-stop the printer.",
      parameters: printerIdParams,
      optional: true,
      execute: async ({ printerId }, config, context) => clientFor(config, printerId).emergencyStop(context.signal),
    }),
  ],
});

type PluginConfig = {
  printers: PrinterConfig[];
};

type PrinterConfig = {
  id: string;
  name?: string;
  type: "octoprint" | "moonraker";
  baseUrl: string;
  apiKeyEnv?: string;
  apiKey?: string;
  cameraId?: string;
};

type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };

function clientFor(config: PluginConfig, printerId: string): PrinterClient {
  const printer = config.printers.find((candidate) => candidate.id === printerId);
  if (!printer) {
    throw new Error(`Unknown printerId: ${printerId}`);
  }
  if (printer.type === "octoprint") {
    return new OctoPrintClient(printer);
  }
  return new MoonrakerClient(printer);
}

abstract class PrinterClient {
  protected readonly config: PrinterConfig;

  protected constructor(config: PrinterConfig) {
    this.config = { ...config, baseUrl: normalizeBaseUrl(config.baseUrl) };
  }

  abstract status(signal?: AbortSignal): Promise<JsonValue>;
  abstract uploadGcode(filePath: string, start: boolean, signal?: AbortSignal): Promise<JsonValue>;
  abstract startPrint(filename: string, signal?: AbortSignal): Promise<JsonValue>;
  abstract pause(signal?: AbortSignal): Promise<JsonValue>;
  abstract resume(signal?: AbortSignal): Promise<JsonValue>;
  abstract cancel(signal?: AbortSignal): Promise<JsonValue>;
  abstract emergencyStop(signal?: AbortSignal): Promise<JsonValue>;

  protected headers(): Record<string, string> {
    const apiKey = this.config.apiKey ?? (this.config.apiKeyEnv ? process.env[this.config.apiKeyEnv] : undefined);
    return apiKey ? { "X-Api-Key": apiKey } : {};
  }

  protected requireGcode(filePath: string): void {
    const suffix = extname(filePath).toLowerCase();
    if (!allowedGcodeSuffixes.has(suffix)) {
      throw new Error("Only .gcode, .gco, and .gc files can be uploaded.");
    }
  }
}

class OctoPrintClient extends PrinterClient {
  constructor(config: PrinterConfig) {
    super(config);
  }

  status(signal?: AbortSignal): Promise<JsonValue> {
    return requestJson(`${this.config.baseUrl}/api/printer`, { headers: this.headers(), signal });
  }

  async uploadGcode(filePath: string, start: boolean, signal?: AbortSignal): Promise<JsonValue> {
    this.requireGcode(filePath);
    const body = await fileFormData(filePath, {
      select: "true",
      print: start ? "true" : "false",
    });
    return requestJson(`${this.config.baseUrl}/api/files/local`, {
      method: "POST",
      headers: this.headers(),
      body,
      signal,
    });
  }

  startPrint(filename: string, signal?: AbortSignal): Promise<JsonValue> {
    return requestJson(`${this.config.baseUrl}/api/files/local/${encodePath(filename)}`, {
      method: "POST",
      headers: jsonHeaders(this.headers()),
      body: JSON.stringify({ command: "select", print: true }),
      signal,
    });
  }

  pause(signal?: AbortSignal): Promise<JsonValue> {
    return this.jobCommand({ command: "pause", action: "pause" }, signal);
  }

  resume(signal?: AbortSignal): Promise<JsonValue> {
    return this.jobCommand({ command: "pause", action: "resume" }, signal);
  }

  cancel(signal?: AbortSignal): Promise<JsonValue> {
    return this.jobCommand({ command: "cancel" }, signal);
  }

  emergencyStop(signal?: AbortSignal): Promise<JsonValue> {
    return requestJson(`${this.config.baseUrl}/api/printer/command`, {
      method: "POST",
      headers: jsonHeaders(this.headers()),
      body: JSON.stringify({ command: "M112" }),
      signal,
    });
  }

  private jobCommand(command: Record<string, string>, signal?: AbortSignal): Promise<JsonValue> {
    return requestJson(`${this.config.baseUrl}/api/job`, {
      method: "POST",
      headers: jsonHeaders(this.headers()),
      body: JSON.stringify(command),
      signal,
    });
  }
}

class MoonrakerClient extends PrinterClient {
  constructor(config: PrinterConfig) {
    super(config);
  }

  status(signal?: AbortSignal): Promise<JsonValue> {
    const query = "print_stats&display_status&virtual_sdcard&toolhead";
    return requestJson(`${this.config.baseUrl}/printer/objects/query?${query}`, {
      headers: this.headers(),
      signal,
    });
  }

  async uploadGcode(filePath: string, start: boolean, signal?: AbortSignal): Promise<JsonValue> {
    this.requireGcode(filePath);
    const body = await fileFormData(filePath, {
      root: "gcodes",
      print: start ? "true" : "false",
    });
    return requestJson(`${this.config.baseUrl}/server/files/upload`, {
      method: "POST",
      headers: this.headers(),
      body,
      signal,
    });
  }

  startPrint(filename: string, signal?: AbortSignal): Promise<JsonValue> {
    return this.postJson("/printer/print/start", { filename }, signal);
  }

  pause(signal?: AbortSignal): Promise<JsonValue> {
    return this.postJson("/printer/print/pause", {}, signal);
  }

  resume(signal?: AbortSignal): Promise<JsonValue> {
    return this.postJson("/printer/print/resume", {}, signal);
  }

  cancel(signal?: AbortSignal): Promise<JsonValue> {
    return this.postJson("/printer/print/cancel", {}, signal);
  }

  emergencyStop(signal?: AbortSignal): Promise<JsonValue> {
    return this.postJson("/printer/emergency_stop", {}, signal);
  }

  private postJson(path: string, data: Record<string, string>, signal?: AbortSignal): Promise<JsonValue> {
    return requestJson(`${this.config.baseUrl}${path}`, {
      method: "POST",
      headers: jsonHeaders(this.headers()),
      body: JSON.stringify(data),
      signal,
    });
  }
}

async function fileFormData(filePath: string, fields: Record<string, string>): Promise<FormData> {
  const data = await readFile(filePath);
  const body = new FormData();
  for (const [key, value] of Object.entries(fields)) {
    body.set(key, value);
  }
  body.set("file", new Blob([data], { type: "application/octet-stream" }), basename(filePath));
  return body;
}

async function requestJson(url: string, init: RequestInit = {}): Promise<JsonValue> {
  const response = await fetch(url, init);
  const text = await response.text();
  const body = parseBody(text);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} from ${url}: ${typeof body === "string" ? body : JSON.stringify(body)}`);
  }
  return body;
}

function parseBody(text: string): JsonValue {
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as JsonValue;
  } catch {
    return text;
  }
}

function jsonHeaders(headers: Record<string, string>): Record<string, string> {
  return { ...headers, "Content-Type": "application/json" };
}

function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "");
}

function encodePath(path: string): string {
  return path.split("/").map(encodeURIComponent).join("/");
}
