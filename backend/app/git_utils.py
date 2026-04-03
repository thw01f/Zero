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
