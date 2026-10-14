"""
共享测试固件。

- ``app``: 会话级 Flask 应用,使用内存 SQLite(见 app/config/test.py),与开发库完全隔离;
  ``create_app`` 过程中 ``Lin.init_app`` 已完成建表与权限同步,固件再补充种子数据。
- ``client``: 每个测试独立的 test_client。
- ``root_headers`` / ``guest_headers``: 已登录用户(超级管理员 root / 游客组 tester)的
  Bearer 认证头,令牌会话内缓存,避免每个用例重复登录。
"""

import os

# 必须在导入 app 之前指定测试环境,create_app 才会加载 TestConfig(内存库)
os.environ["FLASK_ENV"] = "test"

import pytest  # noqa: E402

from app import create_app  # noqa: E402
from app.api.cms.model.group import Group  # noqa: E402
from app.api.cms.model.group_permission import GroupPermission  # noqa: E402
from app.api.cms.model.permission import Permission  # noqa: E402
from app.api.cms.model.user import User  # noqa: E402
from app.api.cms.model.user_group import UserGroup  # noqa: E402
from app.api.cms.model.user_identity import UserIdentity  # noqa: E402
from app.api.v1.model.book import Book  # noqa: E402
from app.lin import db, manager  # noqa: E402

ROOT_USERNAME = "root"
ROOT_PASSWORD = "123456"
GUEST_USERNAME = "tester"
GUEST_PASSWORD = "123456x"

BOOK_PAYLOAD = {
    "title": "测试驱动开发",
    "author": "Kent Beck",
    "summary": "测试驱动开发的实践指南",
    "image": "https://img3.doubanio.com/lpic/s1470003.jpg",
}


def _add_user(username: str, password: str, group_id: int):
    user = manager.user_model()
    user.username = username
    db.session.add(user)
    db.session.flush()
    user.password = password
    user_group = manager.user_group_model()
    user_group.user_id = user.id
    user_group.group_id = group_id
    db.session.add(user_group)
    return user


def _seed() -> None:
    """跑全量迁移（建表 + root/Guest/权限种子），再补测试附加数据：游客用户与一本书。"""

    from flask_migrate import upgrade

    upgrade()
    with db.auto_commit():
        # 迁移种子已提供 Root/Guest 分组与 root 用户；此处按名称解析分组 ID
        guest_group = manager.group_model.get(name="Guest")
        assert guest_group is not None, "迁移种子未生效：缺少 Guest 分组"
        _add_user(GUEST_USERNAME, GUEST_PASSWORD, guest_group.id)
        book = Book(
            title=BOOK_PAYLOAD["title"],
            author=BOOK_PAYLOAD["author"],
            summary=BOOK_PAYLOAD["summary"],
            image=BOOK_PAYLOAD["image"],
        )
        db.session.add(book)


def login(client, username: str, password: str) -> dict:
    rv = client.post("/cms/user/login", json={"username": username, "password": password})
    assert rv.status_code == 200, rv.get_json()
    data = rv.get_json()
    assert data.get("access_token") and data.get("refresh_token")
    return data


def find_user_id(client, headers, username: str) -> int:
    # QueryPageSchema 限制 0 < count < 16,按最大分页翻页查找
    page = 0
    while True:
        rv = client.get("/cms/admin/users", headers=headers, query_string={"count": 15, "page": page})
        assert rv.status_code == 200
        items = rv.get_json()["items"]
        if not items:
            break
        for item in items:
            if item["username"] == username:
                return item["id"]
        page += 1
    raise AssertionError(f"user {username} not found")


def permission_ids_by_module(client, headers, module: str) -> list:
    rv = client.get("/cms/admin/permission", headers=headers)
    assert rv.status_code == 200
    return [p["id"] for p in rv.get_json().get(module, [])]


@pytest.fixture(scope="session")
def app():
    app = create_app(
        group_model=Group,
        user_model=User,
        group_permission_model=GroupPermission,
        permission_model=Permission,
        identity_model=UserIdentity,
        user_group_model=UserGroup,
    )
    with app.app_context():
        _seed()
    return app


@pytest.fixture()
def client(app):
    with app.test_client() as test_client:
        yield test_client


# 注意：函数级作用域——改密会吊销该用户全部旧令牌（token_version 机制），
# 会话级缓存的令牌在相邻测试间会失效，故每个用例重新登录
@pytest.fixture()
def root_auth(app):
    return login(app.test_client(), ROOT_USERNAME, ROOT_PASSWORD)


@pytest.fixture()
def guest_auth(app):
    return login(app.test_client(), GUEST_USERNAME, GUEST_PASSWORD)


@pytest.fixture()
def root_headers(root_auth):
    return {"Authorization": "Bearer " + root_auth["access_token"]}


@pytest.fixture()
def guest_headers(guest_auth):
    return {"Authorization": "Bearer " + guest_auth["access_token"]}
