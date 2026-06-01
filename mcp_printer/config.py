from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "printers": [
        {
            "id": "workbench",
            "name": "Workbench Printer",
            "type": "octoprint",
            "base_url": "http://octopi.local",
            "api_key_env": "OCTOPRINT_API_KEY",
        }
    ]
}


@dataclass(frozen=True)
class PrinterConfig:
    id: str
    name: str
    type: str
    base_url: str
    api_key_env: str | None = None
    api_key: str | None = None
    camera_id: str | None = None


def load_config(path: Path) -> list[PrinterConfig]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    printers = raw.get("printers", [])
    if not isinstance(printers, list):
        raise ValueError("Config field 'printers' must be a list.")

    return [_parse_printer_config(item) for item in printers]


def write_default_config(path: Path) -> None:
    path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")


def _parse_printer_config(item: Any) -> PrinterConfig:
    if not isinstance(item, dict):
        raise ValueError("Each printer config must be an object.")

    required = ("id", "name", "type", "base_url")
    missing = [field for field in required if not item.get(field)]
    if missing:
        raise ValueError(f"Printer config is missing required fields: {', '.join(missing)}")

    printer_type = str(item["type"]).lower()
    if printer_type not in {"octoprint", "moonraker"}:
        raise ValueError(f"Unsupported printer type: {printer_type}")

    return PrinterConfig(
        id=str(item["id"]),
        name=str(item["name"]),
        type=printer_type,
        base_url=str(item["base_url"]).rstrip("/"),
        api_key_env=str(item["api_key_env"]) if item.get("api_key_env") else None,
        api_key=str(item["api_key"]) if item.get("api_key") else None,
        camera_id=str(item["camera_id"]) if item.get("camera_id") else None,
    )
