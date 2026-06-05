"""
Tests de sanité de base — vérifie que l'API démarre et répond.
"""


def test_health_returns_ok(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_health_returns_version(client):
    resp = client.get("/")
    assert "version" in resp.json()
