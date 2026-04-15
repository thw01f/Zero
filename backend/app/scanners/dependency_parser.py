
"""Parse dependency files across ecosystems."""
import json
import re
import os
from pathlib import Path
from typing import TypedDict

class Dependency(TypedDict):
    name: str
    version: str
    ecosystem: str
    file: str
    is_dev: bool

def parse_requirements_txt(path: str) -> list[Dependency]:
    deps = []
    with open(path, errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'^([A-Za-z0-9_\-\.]+)[>=<! ]+([0-9][^\s,;]*)', line)
            if m:
                deps.append(Dependency(name=m.group(1), version=m.group(2),
                                       ecosystem='PyPI', file=path, is_dev=False))
    return deps

def parse_package_json(path: str) -> list[Dependency]:
    deps = []
    with open(path) as f:
        pkg = json.load(f)
    for name, ver in pkg.get('dependencies', {}).items():
        deps.append(Dependency(name=name, version=ver.lstrip('^~>='), ecosystem='npm', file=path, is_dev=False))
    for name, ver in pkg.get('devDependencies', {}).items():
        deps.append(Dependency(name=name, version=ver.lstrip('^~>='), ecosystem='npm', file=path, is_dev=True))
    return deps

def scan_repo_deps(repo_path: str) -> list[Dependency]:
    all_deps = []
    for root, _, files in os.walk(repo_path):
        if '.git' in root or 'node_modules' in root:
            continue
        for f in files:
            fp = os.path.join(root, f)
            if f == 'requirements.txt':
                all_deps.extend(parse_requirements_txt(fp))
            elif f == 'package.json':
                all_deps.extend(parse_package_json(fp))
    return all_deps
