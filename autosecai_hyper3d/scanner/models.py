"""Persistence models for AutoSecAI scan history."""

from __future__ import annotations

import hashlib
import uuid

from django.db import models


class Scan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=48, default="auto")
    code_sha256 = models.CharField(max_length=64)
    issue_count = models.PositiveIntegerField(default=0)
    risk_score = models.PositiveIntegerField(default=0)
    scan_time_ms = models.FloatField(default=0)
    engine_name = models.CharField(max_length=120, default="AutoSecAI Heuristic Scanner")

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def from_result(cls, result: dict, code: str, language: str) -> "Scan":
        summary = result["summary"]
        return cls.objects.create(
            language=language,
            code_sha256=hashlib.sha256(code.encode("utf-8")).hexdigest(),
            issue_count=summary["issue_count"],
            risk_score=summary["risk_score"],
            scan_time_ms=summary["scan_time_ms"],
            engine_name=result["engine"]["name"],
        )


class Finding(models.Model):
    scan = models.ForeignKey(Scan, related_name="findings", on_delete=models.CASCADE)
    external_id = models.CharField(max_length=32)
    type = models.CharField(max_length=120)
    severity = models.CharField(max_length=24)
    cwe = models.CharField(max_length=32)
    owasp = models.CharField(max_length=120)
    line = models.PositiveIntegerField(default=1)
    vulnerable_snippet = models.TextField(blank=True)
    explanation = models.TextField()
    fix = models.TextField()
    secure_example = models.TextField(blank=True)
    confidence = models.CharField(max_length=48, default="Pattern Match")
    learning = models.TextField(blank=True)

    class Meta:
        ordering = ["scan", "line", "severity"]

    @classmethod
    def from_issue(cls, scan: Scan, issue: dict) -> "Finding":
        return cls(
            scan=scan,
            external_id=issue["id"],
            type=issue["type"],
            severity=issue["severity"],
            cwe=issue["cwe"],
            owasp=issue["owasp"],
            line=issue["line"],
            vulnerable_snippet=issue.get("vulnerable_snippet", ""),
            explanation=issue["explanation"],
            fix=issue["fix"],
            secure_example=issue.get("secure_example", ""),
            confidence=issue.get("confidence", "Pattern Match"),
            learning=issue.get("learning", ""),
        )

