"""
管理员:权限清单、用户分页、注册/改密/更新/删除用户、分组 CRUD、权限分发与回收。
"""

from tests.conftest import find_user_id, permission_ids_by_module


def _register(client, headers, username, password="123456x", email=None, group_ids=None):
    payload = {
        "username": username,
        "password": password,
        "confirm_password": password,
        "group_ids": group_ids or [2],  # Guest
    }
    if email:
        payload["email"] = email
    return client.post("/cms/user/register", headers=headers, json=payload)


def test_list_permissions(client, root_headers):
    rv = client.get("/cms/admin/permission", headers=root_headers)
    assert rv.status_code == 200
    data = rv.get_json()
    # sync_permissions 依据代码中的 permission_meta 收集,至少包含日志与图书模块
    assert "日志" in data
    assert "图书" in data
    assert {"id", "name", "module", "mount"} <= set(data["日志"][0])


def test_admin_users_page(client, root_headers):
    rv = client.get("/cms/admin/users", headers=root_headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert {"items", "count", "page", "total", "total_page"} <= set(data)
    usernames = [item["username"] for item in data["items"]]
    # root 组用户不在管理列表中,guest 用户在
    assert "root" not in usernames
    assert "tester" in usernames
    tester = next(item for item in data["items"] if item["username"] == "tester")
    assert tester["groups"][0]["name"] == "Guest"


def test_admin_users_requires_admin(client, guest_headers):
    rv = client.get("/cms/admin/users", headers=guest_headers)
    assert rv.status_code == 401


def test_register_and_delete_user(client, root_headers):
    rv = _register(client, root_headers, "newbie", email="newbie@example.com")
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0

    # 新用户可登录
    rv = client.post("/cms/user/login", json={"username": "newbie", "password": "123456x"})
    assert rv.status_code == 200

    uid = find_user_id(client, root_headers, "newbie")
    rv = client.delete(f"/cms/admin/user/{uid}", headers=root_headers)
    assert rv.status_code == 200

    # 删除后无法再登录(用户不存在)
    rv = client.post("/cms/user/login", json={"username": "newbie", "password": "123456x"})
    assert rv.status_code == 404


def test_register_duplicate_username(client, root_headers):
    _register(client, root_headers, "dupuser")
    rv = _register(client, root_headers, "dupuser")
    assert rv.status_code == 400
    assert rv.get_json()["code"] == 10060

    # 清理
    uid = find_user_id(client, root_headers, "dupuser")
    assert client.delete(f"/cms/admin/user/{uid}", headers=root_headers).status_code == 200


def test_register_password_mismatch(client, root_headers):
    rv = client.post(
        "/cms/user/register",
        headers=root_headers,
        json={
            "username": "badpwd",
            "password": "123456x",
            "confirm_password": "654321x",
            "group_ids": [2],
        },
    )
    assert rv.status_code == 400


def test_admin_change_user_password(client, root_headers):
    _register(client, root_headers, "pwuser", password="abcdef12")
    uid = find_user_id(client, root_headers, "pwuser")

    rv = client.put(
        f"/cms/admin/user/{uid}/password",
        headers=root_headers,
        json={"new_password": "xyz98765", "confirm_password": "xyz98765"},
    )
    assert rv.status_code == 200

    rv = client.post("/cms/user/login", json={"username": "pwuser", "password": "xyz98765"})
    assert rv.status_code == 200


def test_admin_delete_missing_user(client, root_headers):
    rv = client.delete("/cms/admin/user/99999", headers=root_headers)
    assert rv.status_code == 404


def test_admin_cannot_delete_root(client, root_headers):
    # root 属于 Root 组,删除被拒绝(root 不出现在 /cms/admin/users 中,id 由种子顺序确定为 1)
    rv = client.delete("/cms/admin/user/1", headers=root_headers)
    assert rv.status_code == 401


def test_admin_update_user_email(client, root_headers):
    _register(client, root_headers, "mailuser", email="mailuser@example.com")
    uid = find_user_id(client, root_headers, "mailuser")

    rv = client.put(
        f"/cms/admin/user/{uid}",
        headers=root_headers,
        json={"email": "newmail@example.com", "group_ids": [2]},
    )
    assert rv.status_code == 200


def test_group_crud(client, root_headers):
    payload = {"name": "crud-group", "info": "临时分组", "permission_ids": []}
    rv = client.post("/cms/admin/group", headers=root_headers, json=payload)
    assert rv.status_code == 200

    # 同名分组不可重复创建
    rv = client.post("/cms/admin/group", headers=root_headers, json=payload)
    assert rv.status_code == 401

    rv = client.get("/cms/admin/group/all", headers=root_headers)
    group = next(g for g in rv.get_json() if g["name"] == "crud-group")
    gid = group["id"]

    rv = client.get(f"/cms/admin/group/{gid}", headers=root_headers)
    assert rv.status_code == 200
    assert rv.get_json()["permissions"] == []

    rv = client.put(f"/cms/admin/group/{gid}", headers=root_headers, json={"name": "crud-group-2", "info": "改名"})
    assert rv.status_code == 200

    rv = client.delete(f"/cms/admin/group/{gid}", headers=root_headers)
    assert rv.status_code == 200

    rv = client.get(f"/cms/admin/group/{gid}", headers=root_headers)
    assert rv.status_code == 404


def test_cannot_delete_builtin_groups(client, root_headers):
    rv = client.get("/cms/admin/group/all", headers=root_headers)
    # Guest 组不可删除(Root 组不在列表中)
    guest_gid = next(g for g in rv.get_json() if g["name"] == "Guest")["id"]
    rv = client.delete(f"/cms/admin/group/{guest_gid}", headers=root_headers)
    assert rv.status_code == 401


def test_dispatch_and_remove_permissions(client, root_headers, guest_headers):
    permission_ids = permission_ids_by_module(client, root_headers, "日志")

    # 分发日志权限给 Guest 组后,tester 可查询日志
    rv = client.post(
        "/cms/admin/permission/dispatch/batch",
        headers=root_headers,
        json={"group_id": 2, "permission_ids": permission_ids},
    )
    assert rv.status_code == 200
    assert client.get("/cms/log", headers=guest_headers).status_code == 200

    # 回收后立即失去访问权
    rv = client.post(
        "/cms/admin/permission/remove",
        headers=root_headers,
        json={"group_id": 2, "permission_ids": permission_ids},
    )
    assert rv.status_code == 200
    assert client.get("/cms/log", headers=guest_headers).status_code == 401
