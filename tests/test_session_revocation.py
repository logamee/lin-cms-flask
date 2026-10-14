"""
会话撤销（第三轮加固）回归测试:
- logout 吊销当前 access 令牌
- logout 携带 refresh_token 一并吊销
- 改密后旧 access/refresh 全部失效（token_version 机制）
- 管理员重置密码同样吊销用户全部令牌
- 新密码哈希使用 scrypt
"""

from tests.conftest import GUEST_PASSWORD, GUEST_USERNAME, ROOT_PASSWORD, ROOT_USERNAME, find_user_id, login


def test_logout_revokes_access_token(client, app):
    auth = login(client, ROOT_USERNAME, ROOT_PASSWORD)
    headers = {"Authorization": "Bearer " + auth["access_token"]}
    rv = client.post("/cms/user/logout", headers=headers)
    assert rv.status_code == 200
    # 令牌已吊销，再用即 401
    rv = client.get("/cms/user/information", headers=headers)
    assert rv.status_code == 401
    assert "吊销" in rv.get_json().get("message", "")


def test_logout_revokes_refresh_token_too(client):
    auth = login(client, ROOT_USERNAME, ROOT_PASSWORD)
    headers = {"Authorization": "Bearer " + auth["access_token"]}
    rv = client.post("/cms/user/logout", headers=headers, json={"refresh_token": auth["refresh_token"]})
    assert rv.status_code == 200
    # refresh 也被吊销
    rv = client.get("/cms/user/refresh", headers={"Authorization": "Bearer " + auth["refresh_token"]})
    assert rv.status_code in (400, 401, 403, 404)


def test_password_change_revokes_all_tokens(client, app):
    auth = login(client, GUEST_USERNAME, GUEST_PASSWORD)
    old_headers = {"Authorization": "Bearer " + auth["access_token"]}
    # 改密成功
    rv = client.put(
        "/cms/user/change_password",
        headers=old_headers,
        json={"old_password": GUEST_PASSWORD, "new_password": "Zx9kvt7q", "confirm_password": "Zx9kvt7q"},
    )
    assert rv.status_code == 200
    # 旧 access 401
    rv = client.get("/cms/user/information", headers=old_headers)
    assert rv.status_code == 401
    # 旧 refresh 被拒
    rv = client.get("/cms/user/refresh", headers={"Authorization": "Bearer " + auth["refresh_token"]})
    assert rv.status_code in (400, 401, 403, 404)
    # 新密码登录可用；改回保证后续用例
    assert login(client, GUEST_USERNAME, "Zx9kvt7q")["access_token"]
    restore_headers = {"Authorization": "Bearer " + login(client, GUEST_USERNAME, "Zx9kvt7q")["access_token"]}
    rv = client.put(
        "/cms/user/change_password",
        headers=restore_headers,
        json={"old_password": "Zx9kvt7q", "new_password": GUEST_PASSWORD, "confirm_password": GUEST_PASSWORD},
    )
    assert rv.status_code == 200


def test_admin_reset_revokes_user_tokens(client, root_headers):
    # 注册新用户并登录
    rv = client.post(
        "/cms/user/register",
        headers=root_headers,
        json={"username": "revokeu1", "password": "Abcd1234", "confirm_password": "Abcd1234", "group_ids": [2]},
    )
    assert rv.status_code == 200
    auth = login(client, "revokeu1", "Abcd1234")
    old_headers = {"Authorization": "Bearer " + auth["access_token"]}
    # 管理员重置密码
    uid = find_user_id(client, root_headers, "revokeu1")
    rv = client.put(
        f"/cms/admin/user/{uid}/password",
        headers=root_headers,
        json={"new_password": "NewPass99", "confirm_password": "NewPass99"},
    )
    assert rv.status_code == 200
    # 该用户旧令牌全部失效
    rv = client.get("/cms/user/information", headers=old_headers)
    assert rv.status_code == 401
    # 新密码可登录后清理
    client.post("/cms/user/login", json={"username": "revokeu1", "password": "NewPass99"})
    client.delete(f"/cms/admin/user/{uid}", headers=root_headers)


def test_new_password_hash_uses_scrypt(app):
    with app.app_context():
        from app.lin import manager

        user = manager.user_model()
        user.username = "scrypthash"
        from app.lin import db

        db.session.add(user)
        db.session.flush()
        user.password = "Scrypt123"
        identity = manager.identity_model.get(user_id=user.id)
        assert identity is not None
        assert identity.credential.startswith("scrypt")
        user.hard_delete(commit=True)
