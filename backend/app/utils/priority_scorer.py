
"""Priority scoring for remediation ordering."""
from typing import TypedDict

SEVERITY_WEIGHT = {'critical': 40, 'major': 25, 'minor': 10, 'info': 2}
CATEGORY_WEIGHT = {'security': 30, 'vulnerability': 30, 'quality': 10, 'performance': 8, 'maintainability': 5}
OWASP_TOP10 = {'A01','A02','A03','A04','A05','A06','A07','A08','A09','A10'}

class Finding(TypedDict):
    severity: str
    category: str
    owasp: str | None
    cwe: str | None
    has_fix: bool

def priority_score(f: Finding) -> int:
    score = 0
    score += SEVERITY_WEIGHT.get(f.get('severity','info'), 2)
    score += CATEGORY_WEIGHT.get(f.get('category','quality'), 5)
    if f.get('owasp') and any(f['owasp'].startswith(t) for t in OWASP_TOP10):
        score += 15
    if f.get('cwe'):
        score += 10
    if f.get('has_fix'):
        score += 5  # fixable items get priority boost
    return min(score, 100)
