import datetime
import shutil
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict
import git
from .config import settings

ALLOWED_HOSTS = {"github.com", "gitlab.com", "bitbucket.org"}

EXT_LANG = {
    ".py": "python",
    ".js": "javascript", ".ts": "javascript",
    ".jsx": "javascript", ".tsx": "javascript",
    ".java": "java",
}


def validate_repo_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Host not allowed: {parsed.hostname}. Use GitHub, GitLab, or Bitbucket.")


def clone_repo(repo_url: str, dest: str, timeout_s: int = None) -> str:
    validate_repo_url(repo_url)
    timeout_s = timeout_s or settings.clone_timeout_s
    repo = git.Repo.clone_from(
        repo_url, dest,
        depth=1,
        env={"GIT_TERMINAL_PROMPT": "0"},
    )
    # Check size
    total = sum(f.stat().st_size for f in Path(dest).rglob("*") if f.is_file())
    if total > settings.max_repo_size_mb * 1024 * 1024:
        shutil.rmtree(dest, ignore_errors=True)
        raise ValueError(f"Repo exceeds {settings.max_repo_size_mb}MB limit")
    return dest


def detect_language(repo_path: str) -> str:
    counts: Dict[str, int] = defaultdict(int)
    for f in Path(repo_path).rglob("*"):
        if f.is_file() and f.suffix in EXT_LANG:
            counts[EXT_LANG[f.suffix]] += 1
    if not counts:
        return "python"
    return max(counts, key=lambda k: counts[k])


def count_loc(repo_path: str, language: str) -> Dict[str, int]:
    exts = [ext for ext, lang in EXT_LANG.items() if lang == language]
    result: Dict[str, int] = {}
    for f in Path(repo_path).rglob("*"):
        if f.is_file() and f.suffix in exts:
            try:
                lines = f.read_text(errors="replace").splitlines()
                loc = sum(1 for l in lines if l.strip() and not l.strip().startswith(("#", "//", "/*", "*")))
                rel = str(f.relative_to(repo_path))
                result[rel] = loc
            except Exception:
                continue
    return result


def compute_churn(repo_path: str) -> Dict[str, int]:
    churn: Dict[str, int] = defaultdict(int)
    try:
        repo = git.Repo(repo_path)
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=90)
        for commit in repo.iter_commits():
            if commit.committed_datetime < cutoff:
                break
            for file in commit.stats.files:
                churn[file] += 1
    except Exception:
        pass
    return dict(churn)
