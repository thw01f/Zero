"""
Direct code analysis endpoint — no git clone needed.
Runs static scanners on the snippet + LLM analysis.
"""
import asyncio
import subprocess
import tempfile
import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..mcp.llm_layer import analyze_code_snippet

router = APIRouter(prefix="/analyze", tags=["analyze"])

LANG_EXT = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "java": ".java",
    "go": ".go",
    "ruby": ".rb",
    "php": ".php",
    "rust": ".rs",
    "c": ".c",
    "cpp": ".cpp",
    "bash": ".sh",
    "yaml": ".yaml",
    "json": ".json",
    "terraform": ".tf",
    "dockerfile": "Dockerfile",
}


class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "python"
    filename: Optional[str] = None
    mode: str = "full"  # full | security | quality | improve


class StaticResult(BaseModel):
    tool: str
    findings: list


def _run_bandit(code: str, tmpfile: str) -> list:
    try:
        result = subprocess.run(
            ["bandit", "-f", "json", "-q", "--exit-zero", tmpfile],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(result.stdout)
        findings = []
        for r in data.get("results", []):
            findings.append({
                "line": r.get("line_number"),
                "severity": {"HIGH": "critical", "MEDIUM": "major", "LOW": "minor"}.get(r.get("issue_severity", "LOW"), "minor"),
                "rule": r.get("test_id"),
                "message": r.get("issue_text"),
                "tool": "bandit",
            })
        return findings
    except Exception:
        return []


def _run_ruff(code: str, tmpfile: str) -> list:
    try: