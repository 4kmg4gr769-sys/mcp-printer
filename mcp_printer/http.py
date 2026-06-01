from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import request
from urllib.error import HTTPError, URLError


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: Any
    headers: dict[str, str]


class HttpClient:
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        timeout: int = 30,
    ) -> HttpResponse:
        req = request.Request(url, method=method, data=body, headers=headers or {})
        try:
            with request.urlopen(req, timeout=timeout) as res:
                return HttpResponse(res.status, _decode_body(res.read()), dict(res.headers.items()))
        except HTTPError as exc:
            raise RuntimeError(f"HTTP {exc.code} from {url}: {_decode_error(exc)}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc


def json_body(data: dict[str, Any]) -> tuple[bytes, dict[str, str]]:
    return json.dumps(data).encode("utf-8"), {"Content-Type": "application/json"}


def _decode_body(data: bytes) -> Any:
    if not data:
        return None
    text = data.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _decode_error(exc: HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", errors="replace")
    except Exception:
        return exc.reason
