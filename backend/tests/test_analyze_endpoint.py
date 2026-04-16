import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

VULN_CODE = '''
import subprocess
def run(cmd):
    return subprocess.call(cmd, shell=True)  # B602
password = "admin123"  # hardcoded secret
'''

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_models():
    r = client.get("/api/analyze/models")
    assert r.status_code == 200
    data = r.json()
    assert "active_backend" in data
    assert "models" in data


def test_analyze_code_python():
    r = client.post("/api/analyze/code", json={
        "code": VULN_CODE,
        "language": "python",
        "mode": "security"
    })
    assert r.status_code == 200
    data = r.json()
    assert "findings" in data
    assert "overall_score" in data
    assert isinstance(data["findings"], list)
