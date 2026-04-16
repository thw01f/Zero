"""File and content checksums for integrity verification."""
import hashlib
import os

def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def content_md5(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()

def repo_fingerprint(repo_path: str) -> str:
    """Deterministic fingerprint of repo state for cache keys."""
    h = hashlib.sha256()
    for root, dirs, files in sorted(os.walk(repo_path)):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d != 'node_modules')
        for f in sorted(files):
            h.update(os.path.join(root, f).encode())
            try:
                stat = os.stat(os.path.join(root, f))
                h.update(str(stat.st_size).encode())
                h.update(str(stat.st_mtime).encode())
            except Exception:
                pass
    return h.hexdigest()[:16]
