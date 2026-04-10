from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask import jsonify, request


@dataclass(frozen=True)
class ApiError(Exception):
    code: str
    message: str
    status: int = 400
    details: dict[str, Any] | None = None


def error_response(err: ApiError):
    request_id = request.headers.get("X-Request-Id")
    payload = {
        "error": {
            "code": err.code,
            "message": err.message,
            "details": err.details or {},
            "request_id": request_id,
        }
    }
    return jsonify(payload), err.status

