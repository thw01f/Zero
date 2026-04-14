
"""SBOM (Software Bill of Materials) generator."""
import json
import subprocess
import os
from typing import Optional

def generate_cyclonedx(repo_path: str, language: str='auto') -> Optional[dict]:
    """Generate CycloneDX SBOM for a cloned repo."""
    sbom: dict = {
        'bomFormat': 'CycloneDX',
        'specVersion': '1.4',
        'version': 1,
        'components': []
    }

    # Python deps from requirements.txt
    req_file = os.path.join(repo_path, 'requirements.txt')
    if os.path.exists(req_file):
        try:
            with open(req_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '==' in line:
                        name, ver = line.split('==', 1)
                        sbom['components'].append({
                            'type': 'library', 'name': name.strip(),
                            'version': ver.strip(), 'language': 'Python',
                            'purl': f'pkg:pypi/{name.strip().lower()}@{ver.strip()}'
                        })
        except Exception:
            pass

    # Node deps
    pkg_file = os.path.join(repo_path, 'package.json')
    if os.path.exists(pkg_file):
        try:
            with open(pkg_file) as f:
                pkg = json.load(f)
            for name, ver in {**pkg.get('dependencies',{}), **pkg.get('devDependencies',{})}.items():
                sbom['components'].append({
                    'type': 'library', 'name': name, 'version': ver.lstrip('^~'),
                    'language': 'JavaScript',
                    'purl': f'pkg:npm/{name}@{ver.lstrip("^~")}'
                })
        except Exception:
            pass

    return sbom
