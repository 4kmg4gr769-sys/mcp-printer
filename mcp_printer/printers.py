from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from .config import PrinterConfig
from .http import HttpClient, json_body


ALLOWED_GCODE_SUFFIXES = {".gcode", ".gco", ".gc"}


class PrinterClient(Protocol):
    def status(self) -> dict[str, Any]:
        ...

    def upload_gcode(self, file_path: Path, start: bool) -> dict[str, Any]:
        ...

    def start_print(self, filename: str) -> dict[str, Any]:
        ...

    def pause(self) -> dict[str, Any]:
        ...

    def resume(self) -> dict[str, Any]:
        ...

    def cancel(self) -> dict[str, Any]:
        ...

    def emergency_stop(self) -> dict[str, Any]:
        ...


def build_client(config: PrinterConfig, http: HttpClient | None = None) -> PrinterClient:
    if config.type == "octoprint":
        return OctoPrintClient(config, http or HttpClient())
    if config.type == "moonraker":
        return MoonrakerClient(config, http or HttpClient())
    raise ValueError(f"Unsupported printer type: {config.type}")


class BasePrinterClient:
    def __init__(self, config: PrinterConfig, http: HttpClient) -> None:
        self.config = config
        self.http = http

    @property
    def api_key(self) -> str | None:
        if self.config.api_key:
            return self.config.api_key
        if self.config.api_key_env:
            return os.environ.get(self.config.api_key_env)
        return None

    def require_gcode(self, file_path: Path) -> None:
        if file_path.suffix.lower() not in ALLOWED_GCODE_SUFFIXES:
            raise ValueError("Only .gcode, .gco, and .gc files can be uploaded.")
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"G-code file not found: {file_path}")


class OctoPrintClient(BasePrinterClient):
    def status(self) -> dict[str, Any]:
        return self.http.request("GET", f"{self.config.base_url}/api/printer", headers=self._headers()).body

    def upload_gcode(self, file_path: Path, start: bool) -> dict[str, Any]:
        self.require_gcode(file_path)
        boundary = f"mcp-printer-{uuid4().hex}"
        fields = {"select": "true", "print": "true" if start else "false"}
        body = _multipart_body(boundary, fields, "file", file_path)
        headers = self._headers()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        return self.http.request(
            "POST",
            f"{self.config.base_url}/api/files/local",
            headers=headers,
            body=body,
            timeout=120,
        ).body

    def start_print(self, filename: str) -> dict[str, Any]:
        body, headers = json_body({"command": "select", "print": True})
        headers.update(self._headers())
        return self.http.request(
            "POST",
            f"{self.config.base_url}/api/files/local/{filename}",
            headers=headers,
            body=body,
        ).body

    def pause(self) -> dict[str, Any]:
        return self._job_command({"command": "pause", "action": "pause"})

    def resume(self) -> dict[str, Any]:
        return self._job_command({"command": "pause", "action": "resume"})

    def cancel(self) -> dict[str, Any]:
        return self._job_command({"command": "cancel"})

    def emergency_stop(self) -> dict[str, Any]:
        body, headers = json_body({"command": "M112"})
        headers.update(self._headers())
        return self.http.request("POST", f"{self.config.base_url}/api/printer/command", headers=headers, body=body).body

    def _job_command(self, command: dict[str, Any]) -> dict[str, Any]:
        body, headers = json_body(command)
        headers.update(self._headers())
        return self.http.request("POST", f"{self.config.base_url}/api/job", headers=headers, body=body).body

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers


class MoonrakerClient(BasePrinterClient):
    def status(self) -> dict[str, Any]:
        url = (
            f"{self.config.base_url}/printer/objects/query?"
            "print_stats&display_status&virtual_sdcard&toolhead"
        )
        return self.http.request("GET", url, headers=self._headers()).body

    def upload_gcode(self, file_path: Path, start: bool) -> dict[str, Any]:
        self.require_gcode(file_path)
        boundary = f"mcp-printer-{uuid4().hex}"
        fields = {"root": "gcodes", "print": "true" if start else "false"}
        body = _multipart_body(boundary, fields, "file", file_path)
        headers = self._headers()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        return self.http.request(
            "POST",
            f"{self.config.base_url}/server/files/upload",
            headers=headers,
            body=body,
            timeout=120,
        ).body

    def start_print(self, filename: str) -> dict[str, Any]:
        return self._post_json("/printer/print/start", {"filename": filename})

    def pause(self) -> dict[str, Any]:
        return self._post_json("/printer/print/pause", {})

    def resume(self) -> dict[str, Any]:
        return self._post_json("/printer/print/resume", {})

    def cancel(self) -> dict[str, Any]:
        return self._post_json("/printer/print/cancel", {})

    def emergency_stop(self) -> dict[str, Any]:
        return self._post_json("/printer/emergency_stop", {})

    def _post_json(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        body, headers = json_body(data)
        headers.update(self._headers())
        return self.http.request("POST", f"{self.config.base_url}{path}", headers=headers, body=body).body

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers


def _multipart_body(boundary: str, fields: dict[str, str], file_field: str, file_path: Path) -> bytes:
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(f"{value}\r\n".encode("utf-8"))

    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    chunks.append(f"--{boundary}\r\n".encode("utf-8"))
    chunks.append(
        (
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8")
    )
    chunks.append(file_path.read_bytes())
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks)
