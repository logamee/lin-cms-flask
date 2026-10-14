"""
认证相关:登录成功/失败、参数校验、令牌刷新、验证码、未认证访问。
"""


def test_login_success(client):
    rv = client.post("/cms/user/login", json={"username": "root", "password": "123456"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["access_token"]
    assert data["refresh_token"]


def test_login_wrong_password(client):
    rv = client.post("/cms/user/login", json={"username": "root", "password": "wrong-password"})
    assert rv.status_code == 400
    assert rv.get_json()["code"] == 10030


def test_login_unknown_user(client):
    rv = client.post("/cms/user/login", json={"username": "nobody", "password": "123456"})
    assert rv.status_code == 404
    assert rv.get_json()["code"] == 10021


def test_login_missing_fields_rejected_by_validator(client):
    rv = client.post("/cms/user/login", json={})
    assert rv.status_code == 400


def test_protected_endpoint_without_token(client):
    rv = client.get("/cms/user/information")
    assert rv.status_code == 401


def test_refresh_token_roundtrip(client, root_auth):
    rv = client.get("/cms/user/refresh", headers={"Authorization": "Bearer " + root_auth["refresh_token"]})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["access_token"]
    assert data["refresh_token"]


def test_refresh_rejects_access_token(client, root_auth):
    # access_token 不具备 refresh 作用域
    rv = client.get("/cms/user/refresh", headers={"Authorization": "Bearer " + root_auth["access_token"]})
    assert rv.status_code == 400


def test_captcha(client):
    rv = client.get("/cms/user/captcha")
    assert rv.status_code == 200
    assert set(rv.get_json()) == {"tag", "image"}
