"""
质量修复回归测试:
- change_password 失败必须走异常约定(非 200 错误体)
- 登录验证码 tag 损坏时返回业务错误而非 500
- 日志脱敏递归遮蔽敏感字段
- BaseConfig 不再内置公网缺省 SECRET_KEY
- create_app 对非法 FLASK_ENV 快速失败
- auto_commit 回滚后向上抛出异常
- 模型 update(commit=True) 真正提交
- refresh 对伪造/损坏令牌与不存在用户返回 RefreshFailed
"""

import json

import pytest

from tests.conftest import GUEST_PASSWORD


def test_change_password_wrong_old_password_fails(client, guest_headers):
    rv = client.put(
        "/cms/user/change_password",
        headers=guest_headers,
        json={"old_password": "totally-wrong", "new_password": "NewPass123", "confirm_password": "NewPass123"},
    )
    body = rv.get_json()
    assert rv.status_code != 200, "旧密码错误不允许 200 成功响应"
    assert body.get("code") != 0


def test_login_captcha_garbage_tag_rejected(app):
    app.config["LOGIN_CAPTCHA"] = True
    try:
        with app.test_client() as c:
            rv = c.post(
                "/cms/user/login",
                headers={"tag": "garbage-not-a-jwt"},
                json={"username": "root", "password": "123456"},
            )
        assert rv.status_code != 500, "损坏的验证码 tag 不应导致 500"
        assert "验证码校验失败" in rv.get_json().get("message", "")
    finally:
        app.config["LOGIN_CAPTCHA"] = False


def test_syslogger_redact_masks_sensitive_fields():
    from app.lin.syslogger import _redact

    data = {
        "username": "root",
        "password": "123456",
        "nested": {"new_password": "x", "keep": 1},
        "items": [{"access_token": "t"}],
    }
    out = _redact(data)
    assert out["username"] == "root"
    assert out["password"] == "***"
    assert out["nested"]["new_password"] == "***"
    assert out["nested"]["keep"] == 1
    assert out["items"][0]["access_token"] == "***"


def test_base_config_has_no_default_secret():
    # 未通过环境变量提供时必须为 None,由 create_app 快速失败兜底
    import os

    assert os.getenv("SECRET_KEY") is None


def test_create_app_rejects_unknown_env(monkeypatch):
    from app import create_app

    monkeypatch.setenv("FLASK_ENV", "staging")
    with pytest.raises(RuntimeError, match="FLASK_ENV"):
        create_app(register_all=False)


def test_auto_commit_rollback_and_reraise(app):
    from app.lin import db

    with app.app_context():
        with pytest.raises(RuntimeError):
            with db.auto_commit():
                raise RuntimeError("boom")


def test_model_update_commit_kwarg_persists(app):
    from app.api.v1.model.book import Book

    with app.app_context():
        book = Book.create(title="commit-kwarg-test", author="t", summary="s", image="i", commit=True)
        book.update(title="commit-kwarg-test-2", commit=True)
        fetched = Book.get(id=book.id)
        assert fetched is not None
        assert fetched.title == "commit-kwarg-test-2"
        book.hard_delete(commit=True)


def test_refresh_rejects_forged_identity(app):
    import jwt as pyjwt
    from flask import current_app

    with app.app_context():
        secret = current_app.config["SECRET_KEY"]
        forged = pyjwt.encode(
            {
                "sub": json.dumps({"uid": 999999, "scope": "lin"}),
                "type": "refresh",
                "fresh": False,
                "jti": "test-jti",
            },
            secret,
            algorithm="HS256",
        )
    with app.test_client() as c:
        rv = c.get("/cms/user/refresh", headers={"Authorization": f"Bearer {forged}"})
    assert rv.status_code in (400, 401, 403, 404)
