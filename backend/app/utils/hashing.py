"""Secure hashing utilities."""
import hashlib, hmac, secrets

def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def hmac_sha256(key: str, message: str) -> str:
    return hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()

def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)

def constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())
