import asyncio
import logging
from typing import Callable, Awaitable, List
from .base import BaseTool, Finding

logger = logging.getLogger(__name__)

ALL_TOOLS: List[BaseTool] = []


def register_tools():
    """Import and register all tools."""
    from .semgrep import SemgrepTool
    from .bandit import BanditTool
    from .ruff_tool import RuffTool
    from .vulture import VultureTool
    from .gitleaks import GitleaksTool
    from .detect_secrets import DetectSecretsTool
    from .trivy import TrivyTool
    from .osv_scanner import OSVScannerTool
    from .pip_audit import PipAuditTool
    from .npm_audit import NpmAuditTool
    from .lizard_tool import LizardTool
    from .radon_tool import RadonTool
    from .eslint import ESLintTool
    from .pmd import PMDTool
    from .spotbugs import SpotBugsTool
    from .checkov_tool import CheckovTool
    from .hadolint_tool import HadolintTool
    from .tfsec_tool import TfsecTool
    from .env_checker import EnvCheckerTool

    ALL_TOOLS.extend([
        SemgrepTool(), BanditTool(), RuffTool(), VultureTool(),
        GitleaksTool(), DetectSecretsTool(),
        TrivyTool(), OSVScannerTool(), PipAuditTool(), NpmAuditTool(),
        LizardTool(), RadonTool(),
        ESLintTool(), PMDTool(), SpotBugsTool(),
        CheckovTool(), HadolintTool(), TfsecTool(), EnvCheckerTool(),
    ])


async def safe_run(tool: BaseTool, repo_path: str, language: str) -> List[Finding]:
    try:
        return await tool.run(repo_path, language)
    except Exception as e:
        logger.warning(f"Tool {tool.name} failed: {e}")
        return []


async def run_all(
    repo_path: str,
    language: str,
    ws_send: Callable[[dict], Awaitable[None]],
) -> List[Finding]:
    applicable = [t for t in ALL_TOOLS if t.is_applicable(language) and t._available()]
    if not applicable:
        return []

    tasks = {tool.name: asyncio.create_task(safe_run(tool, repo_path, language))
             for tool in applicable}

    results: List[Finding] = []
    done_count = 0
    total = len(tasks)

    for name, task in tasks.items():
        findings = await task
        results.extend(findings)
        done_count += 1
        progress = 10 + int((done_count / total) * 40)
        try:
            await ws_send({
                "event": "scanner_done",
                "scanner": name,
                "count": len(findings),
                "progress": progress,
            })
        except Exception:
            pass

    return results
