from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from .config import PrinterConfig
from .printers import build_client

JsonObject = dict[str, Any]


class PrinterMcpServer:
    def __init__(self, printers: list[PrinterConfig]) -> None:
        self.printers = {printer.id: printer for printer in printers}
        self.tools: dict[str, Callable[[JsonObject], Any]] = {
            "printer_list": self.printer_list,
            "printer_status": self.printer_status,
            "printer_upload_gcode": self.printer_upload_gcode,
            "printer_start_print": self.printer_start_print,
            "printer_pause": self.printer_pause,
            "printer_resume": self.printer_resume,
            "printer_cancel": self.printer_cancel,
            "printer_emergency_stop": self.printer_emergency_stop,
        }

    def run(self) -> None:
        for line in sys.stdin:
            try:
                message = json.loads(line)
                response = self.handle(message)
            except Exception as exc:
                response = self.error(None, -32603, str(exc))
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

    def handle(self, message: JsonObject) -> JsonObject | None:
        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params") or {}

        if method == "initialize":
            return self.result(
                request_id,
                {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "mcp-printer",
                        "version": "0.1.0",
                        "credits": "Steve Villari and Villocity Labs",
                    },
                    "capabilities": {"tools": {}},
                },
            )
        if method == "notifications/initialized":
            return None
        if method == "tools/list":
            return self.result(request_id, {"tools": tool_definitions()})
        if method == "tools/call":
            return self.call_tool(request_id, params)

        return self.error(request_id, -32601, f"Unknown method: {method}")

    def call_tool(self, request_id: Any, params: JsonObject) -> JsonObject:
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name not in self.tools:
            return self.error(request_id, -32602, f"Unknown tool: {name}")

        try:
            payload = self.tools[name](arguments)
            return self.result(request_id, {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]})
        except Exception as exc:
            return self.error(request_id, -32000, str(exc))

    def printer_list(self, _: JsonObject) -> list[JsonObject]:
        return [printer_summary(printer) for printer in self.printers.values()]

    def printer_status(self, args: JsonObject) -> JsonObject:
        return self.client(args).status()

    def printer_upload_gcode(self, args: JsonObject) -> JsonObject:
        file_path = Path(required(args, "file_path")).expanduser()
        start = bool(args.get("start", False))
        return self.client(args).upload_gcode(file_path, start)

    def printer_start_print(self, args: JsonObject) -> JsonObject:
        return self.client(args).start_print(required(args, "filename"))

    def printer_pause(self, args: JsonObject) -> JsonObject:
        return self.client(args).pause()

    def printer_resume(self, args: JsonObject) -> JsonObject:
        return self.client(args).resume()

    def printer_cancel(self, args: JsonObject) -> JsonObject:
        return self.client(args).cancel()

    def printer_emergency_stop(self, args: JsonObject) -> JsonObject:
        return self.client(args).emergency_stop()

    def client(self, args: JsonObject):
        printer_id = required(args, "printer_id")
        if printer_id not in self.printers:
            raise ValueError(f"Unknown printer_id: {printer_id}")
        return build_client(self.printers[printer_id])

    @staticmethod
    def result(request_id: Any, result: JsonObject) -> JsonObject:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def error(request_id: Any, code: int, message: str) -> JsonObject:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def required(args: JsonObject, name: str) -> str:
    value = args.get(name)
    if not value:
        raise ValueError(f"Missing required argument: {name}")
    return str(value)


def printer_summary(printer: PrinterConfig) -> JsonObject:
    summary: JsonObject = {
        "id": printer.id,
        "name": printer.name,
        "type": printer.type,
        "base_url": printer.base_url,
    }
    if printer.camera_id:
        summary["camera_id"] = printer.camera_id
    return summary


def tool_definitions() -> list[JsonObject]:
    return [
        {
            "name": "printer_list",
            "description": "List configured 3D printers.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "printer_status",
            "description": "Get the current status of a configured 3D printer.",
            "inputSchema": _printer_schema(),
        },
        {
            "name": "printer_upload_gcode",
            "description": "Upload a local G-code file to a printer, optionally starting the print.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "printer_id": {"type": "string"},
                    "file_path": {"type": "string"},
                    "start": {"type": "boolean", "default": False},
                },
                "required": ["printer_id", "file_path"],
                "additionalProperties": False,
            },
        },
        {
            "name": "printer_start_print",
            "description": "Start printing an already-uploaded file.",
            "inputSchema": {
                "type": "object",
                "properties": {"printer_id": {"type": "string"}, "filename": {"type": "string"}},
                "required": ["printer_id", "filename"],
                "additionalProperties": False,
            },
        },
        _command_tool("printer_pause", "Pause the active print."),
        _command_tool("printer_resume", "Resume a paused print."),
        _command_tool("printer_cancel", "Cancel the active print."),
        _command_tool("printer_emergency_stop", "Immediately emergency-stop the printer."),
    ]


def _printer_schema() -> JsonObject:
    return {
        "type": "object",
        "properties": {"printer_id": {"type": "string"}},
        "required": ["printer_id"],
        "additionalProperties": False,
    }


def _command_tool(name: str, description: str) -> JsonObject:
    return {"name": name, "description": description, "inputSchema": _printer_schema()}
