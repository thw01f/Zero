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
        result = subprocess.run(
            ["ruff", "check", "--output-format", "json", tmpfile],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(result.stdout) if result.stdout.strip() else []
        findings = []
        for r in data:
            findings.append({
                "line": r.get("location", {}).get("row"),
                "severity": "minor",
                "rule": r.get("code"),
                "message": r.get("message"),
                "tool": "ruff",
            })
        return findings
    except Exception:
        return []


def _run_lizard(code: str, tmpfile: str) -> list:
    try:
        import lizard
        result = lizard.analyze_file(tmpfile)
        findings = []
        for fn in result.function_list:
            if fn.cyclomatic_complexity > 10:
                sev = "critical" if fn.cyclomatic_complexity > 20 else "major"
                findings.append({
                    "line": fn.start_line,
                    "severity": sev,
                    "rule": "high-complexity",
                    "message": f"Function '{fn.name}' has cyclomatic complexity {fn.cyclomatic_complexity} (threshold: 10)",
                    "tool": "lizard",
                })
        return findings
    except Exception:
        return []


@router.post("/code")
async def analyze_code(req: CodeAnalysisRequest):
    if len(req.code) > 100_000:
        raise HTTPException(status_code=400, detail="Code too large (max 100KB)")
    if not req.code.strip():
        raise HTTPException(status_code=400, detail="Empty code")

    lang = req.language.lower()
    ext = LANG_EXT.get(lang, ".txt")
    filename = req.filename or f"snippet{ext}"

    static_findings = []

    # Run static tools in temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False) as tf:
        tf.write(req.code)
        tmppath = tf.name

    try:
        loop = asyncio.get_event_loop()
        if lang == "python":
            bandit_res, ruff_res, lizard_res = await asyncio.gather(
                loop.run_in_executor(None, _run_bandit, req.code, tmppath),
                loop.run_in_executor(None, _run_ruff, req.code, tmppath),
                loop.run_in_executor(None, _run_lizard, req.code, tmppath),
            )
            static_findings.extend(bandit_res)
            static_findings.extend(ruff_res)
            static_findings.extend(lizard_res)
    finally:
        try:
            os.unlink(tmppath)
        except Exception:
            pass

    # LLM deep analysis
    llm_result = await analyze_code_snippet(req.code, req.language, filename, req.mode)

    # Merge static findings into LLM findings (deduplicate by line+message)
    seen = set()
    merged_findings = []
    for f in llm_result.get("findings", []):
        key = (f.get("line"), f.get("rule"))
        if key not in seen:
            seen.add(key)
            merged_findings.append(f)

    for sf in static_findings:
        key = (sf.get("line"), sf.get("rule"))
        if key not in seen:
            seen.add(key)
            merged_findings.append({
                "line": sf.get("line"),
                "severity": sf.get("severity"),
                "category": "security" if sf.get("tool") == "bandit" else "quality",
                "rule": sf.get("rule"),
                "message": sf.get("message"),
                "explanation": None,
                "cwe": None,
                "owasp": None,
                "tool": sf.get("tool"),
            })

    # Sort by severity
    sev_order = {"critical": 0, "major": 1, "minor": 2, "info": 3}
    merged_findings.sort(key=lambda x: sev_order.get(x.get("severity", "info"), 3))

    return {
        **llm_result,
        "findings": merged_findings,
        "static_tools_run": ["bandit", "ruff", "lizard"] if lang == "python" else [],
        "language": req.language,
        "filename": filename,
        "mode": req.mode,
        "loc": len(req.code.splitlines()),
    }


class ExplainRequest(BaseModel):
    file_path: str = ""
    line: int = 0
    severity: str = "info"
    rule_id: Optional[str] = None
    message: str = ""
    code_context: Optional[str] = None
    language: str = "unknown"
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None


@router.post("/explain")
async def explain_finding_endpoint(req: ExplainRequest):
    from ..mcp.llm_layer import explain_finding
    finding = {
        "file_path": req.file_path, "line": req.line, "severity": req.severity,
        "rule_id": req.rule_id, "message": req.message,
        "cwe_id": req.cwe_id, "owasp_category": req.owasp_category,
    }
    return await explain_finding(finding, req.code_context, req.language)


@router.get("/models")
async def list_models():
    """List available LLM backends."""
    from ..config import settings
    models = []
    # Check Ollama
    try:
        import httpx
        resp = httpx.get(f"{settings.ollama_url}/api/tags", timeout=3)
        if resp.status_code == 200:
            for m in resp.json().get("models", []):
                models.append({"name": m["name"], "backend": "ollama", "size": m.get("size")})
    except Exception:
        pass
    # Anthropic
    if not settings.anthropic_api_key.startswith("sk-ant-your") and settings.anthropic_api_key != "sk-ant-changeme":
        models.append({"name": settings.model, "backend": "anthropic", "size": None})

    from ..mcp.llm_layer import _is_local
    is_local = _is_local()
    return {
        "active_backend": "ollama" if is_local else "anthropic",
        "active_model": settings.ollama_model if is_local else settings.model,
        "models": models,
    }
