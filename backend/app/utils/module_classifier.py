"""Classify repository files into modules/components."""
import re
from pathlib import Path

CATEGORY_RULES = [
    (r'test[s]?/|_test\.|test_|spec/', 'tests'),
    (r'doc[s]?/|\.md$|\.rst$|\.txt$', 'docs'),
    (r'config|settings|\.env|\.cfg|\.ini$|\.toml$', 'config'),
    (r'migration[s]?/|alembic/', 'migrations'),
    (r'static/|public/|assets/', 'static'),
    (r'template[s]?/|view[s]?/', 'templates'),
    (r'api/|route[s]?/|endpoint[s]?/', 'api'),
    (r'model[s]?/|schema[s]?/|orm/', 'models'),
    (r'util[s]?/|helper[s]?/|lib/', 'utils'),
    (r'service[s]?/|manager[s]?/', 'services'),
    (r'celery|task[s]?/|worker[s]?/', 'workers'),
    (r'docker|container|deploy/', 'infra'),
]

def classify_file(path: str) -> str:
    for pattern, category in CATEGORY_RULES:
        if re.search(pattern, path, re.IGNORECASE):
            return category
    return 'core'

def group_files_by_module(paths: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for p in paths:
        cat = classify_file(p)
        groups.setdefault(cat, []).append(p)
    return groups
