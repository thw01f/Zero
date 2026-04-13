
"""Validate GitHub repo URL before cloning."""
import re
import ipaddress
from urllib.parse import urlparse

ALLOWED_HOSTS = {'github.com', 'gitlab.com', 'bitbucket.org'}
PRIVATE_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('::1/128'),
]

def validate_repo_url(url: str) -> tuple[bool, str]:
    """Returns (is_valid, error_message)."""
    try:
        p = urlparse(url)
    except Exception:
        return False, "Invalid URL format"
    if p.scheme not in ('http', 'https'):
        return False, "Only http/https URLs allowed"
    host = p.hostname or ''
    if host not in ALLOWED_HOSTS:
        return False, f"Host '{host}' not in allowlist: {ALLOWED_HOSTS}"
    # SSRF guard
    try:
        addr = ipaddress.ip_address(host)
        for net in PRIVATE_RANGES:
            if addr in net:
                return False, "SSRF: private IP blocked"
    except ValueError:
        pass  # hostname, not raw IP — OK
    if not re.match(r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$', p.path.strip('/')):
        return False, "Invalid repo path format"
    return True, ""
