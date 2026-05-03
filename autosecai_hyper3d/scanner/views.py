"""Django API views for AutoSecAI scans."""

from __future__ import annotations

import json

from django.db import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .engine import scan_source
from .models import Finding, Scan


def _cors(response: JsonResponse) -> JsonResponse:
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@require_http_methods(["GET"])
def health(_request):
    return _cors(
        JsonResponse(
            {
                "status": "online",
                "system": "AutoSecAI // HYPER 3D MODE",
                "engine": "heuristic-owasp-prototype",
            }
        )
    )


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def scan_code(request):
    if request.method == "OPTIONS":
        return _cors(JsonResponse({"ok": True}))

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return _cors(JsonResponse({"error": "Invalid JSON body."}, status=400))

    code = payload.get("code")
    language = payload.get("language", "auto")
    learning_mode = bool(payload.get("learning_mode", True))

    if not isinstance(code, str):
        return _cors(JsonResponse({"error": "`code` must be a string."}, status=400))

    if len(code) > 250_000:
        return _cors(
            JsonResponse(
                {"error": "Code payload is too large for the prototype scanner."},
                status=413,
            )
        )

    result = scan_source(code=code, language=language, learning_mode=learning_mode)
    result["scan_id"] = _persist_scan(result, code, language)
    return _cors(JsonResponse(result, json_dumps_params={"indent": 2}))


def _persist_scan(result: dict, code: str, language: str) -> str | None:
    try:
        scan = Scan.from_result(result=result, code=code, language=language)
        Finding.objects.bulk_create(
            [Finding.from_issue(scan=scan, issue=issue) for issue in result["issues"]]
        )
    except (OperationalError, ProgrammingError):
        return None
    return str(scan.id)
