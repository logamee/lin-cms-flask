"""存活探针：/health 无需认证，返回状态与版本号。"""


def test_health_ok(client):
    rv = client.get("/health")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == "ok"
    assert data["version"]
