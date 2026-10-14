"""
普通用户:查询个人信息、更新资料、修改密码、查询自身权限。
"""

from tests.conftest import GUEST_PASSWORD, GUEST_USERNAME, login


def test_get_information(client, root_headers):
    rv = client.get("/cms/user/information", headers=root_headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["username"] == "root"


def test_update_own_nickname(client, root_headers):
    rv = client.put("/cms/user", headers=root_headers, json={"nickname": "rooter"})
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0

    rv = client.get("/cms/user/information", headers=root_headers)
    assert rv.get_json()["nickname"] == "rooter"


def test_update_own_info_with_invalid_nickname(client, root_headers):
    # nickname 约束: 2~10 位
    rv = client.put("/cms/user", headers=root_headers, json={"nickname": "x"})
    assert rv.status_code == 400


def test_get_allowed_permissions(client, root_headers):
    rv = client.get("/cms/user/permissions", headers=root_headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["admin"] is True
    assert isinstance(data["permissions"], list)


def test_change_password_and_relogin(client, app):
    new_password = "z0o9x8w7"
    headers = {"Authorization": "Bearer " + login(app.test_client(), GUEST_USERNAME, GUEST_PASSWORD)["access_token"]}

    rv = client.put(
        "/cms/user/change_password",
        headers=headers,
        json={"old_password": GUEST_PASSWORD, "new_password": new_password, "confirm_password": new_password},
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0

    # 新密码可登录,旧密码被拒绝
    assert login(app.test_client(), GUEST_USERNAME, new_password)["access_token"]
    rv = app.test_client().post("/cms/user/login", json={"username": GUEST_USERNAME, "password": GUEST_PASSWORD})
    assert rv.status_code == 400

    # 改回原密码,保证其他用例不受影响
    # 改密后旧令牌已被 token_version 机制吊销，须用新密码重新登录拿令牌
    headers = {"Authorization": "Bearer " + login(app.test_client(), GUEST_USERNAME, new_password)["access_token"]}
    rv = client.put(
        "/cms/user/change_password",
        headers=headers,
        json={"old_password": new_password, "new_password": GUEST_PASSWORD, "confirm_password": GUEST_PASSWORD},
    )
    assert rv.status_code == 200


def test_change_password_mismatch(client, guest_headers):
    rv = client.put(
        "/cms/user/change_password",
        headers=guest_headers,
        json={"old_password": GUEST_PASSWORD, "new_password": "abcd1234", "confirm_password": "different"},
    )
    assert rv.status_code == 400
